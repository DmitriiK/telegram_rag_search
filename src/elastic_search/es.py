import json
from typing import Iterable, Dict, List
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

import src.config as cfg
from src.data_classes import TelegaMessage
from src.read_telega_dump import telega_dump_parse_essential

es_client = Elasticsearch(cfg.es_url) 
# es_client.info()


def get_st_model():
    model = SentenceTransformer(cfg.sent_tranformer_model_name)
    return model


def index_json_file(file_path: str, index_name, recreate_index=True):
    with open(file_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    index_docs(docs, index_name, recreate_index)


def index_docs(docs: Iterable[Dict], index_name, recreate_index=True):
    ind_set = cfg.read_index_settings(index_name)
    if recreate_index:
        es_client.indices.delete(index=index_name, ignore_unavailable=True)
        es_client.indices.create(index=index_name, body=ind_set)
    
    ind_flds = ind_set['mappings']['properties']
    vector_flds = [f for f in ind_flds if ind_flds[f]['type'] == 'dense_vector']
    if vector_flds:
        model = get_st_model()
    pk_fields = cfg.index_pk_fields.get(index_name)
    for d in tqdm(docs):
        d['chat_id'] = cfg.telegram_group_id
        doc_id = None
        if pk_fields:
            doc_id = ';'.join([str(d[x]) for x in pk_fields])
        for ftv in vector_flds:
            fld_to_encode = ftv[0: len(ftv) - len('_vector')]  # lets rely on this convention
            if fld_to_encode in d:
                d[ftv] = model.encode(d[fld_to_encode]).tolist()
        es_client.index(index=index_name, id=doc_id, document=d)


def load_messages_from_dump():
    messages_dump_path = cfg.messages_dump_path
    msgs = telega_dump_parse_essential(dump_path=messages_dump_path)
    subset = [msg.model_dump() for msg in msgs]
    # subset = (x for x in subset if x['msg_date']> datetime(2024,1, 1))
    # encoding = tiktoken.encoding_for_model(cfg.llm_model)
    index_docs(docs=subset, index_name=cfg.index_name_messages, recreate_index=True)


def load_from_json_to_es(json_file_path: str, es_index_name: str):
    with open(json_file_path, 'r') as f:
        docs = json.load(f)
    index_docs(docs, index_name=es_index_name, recreate_index=True)


def hybrid_search(search_term: str, knn_search_field: str, text_search_field: str, index_name: str, output_fields: List[str] = None,
                  size: int = 10, chat_id: int = None):
    chat_id = chat_id or cfg.telegram_group_id
    model = get_st_model()
    vector = model.encode(search_term)

    knn_query = {
        "field": knn_search_field,
        "query_vector": vector,
        "k": size,
        "num_candidates": 10000,
        "boost": 0.5
    }

    keyword_query = {
        "bool": {
            "must": {
                "multi_match": {
                    "query":  search_term,
                    "fields": [text_search_field],
                    "type": "best_fields",
                    "boost": 0.5
                }
            }
        }
    }

    if not output_fields:
        ind_flds = cfg.read_index_settings(index_name)['mappings']['properties']
        output_fields = [f for f in ind_flds
                         if ind_flds[f]['type'] != 'dense_vector']
    search_query = {
        "knn": knn_query,
        "query": keyword_query,
        "size": size,
        "_source": output_fields
    }

    es_results = es_client.search(
        index=index_name,
        body=search_query
    )
    
    result_docs = [{'doc': hit['_source'], 'score': hit['_score']} for hit in es_results['hits']['hits']]

    return result_docs


def simple_search(search_term: str, search_field: str, index_name: str, output_fields: List[str] = None, min_score: float = 2, size: int = 20):
    if not output_fields:
        ind_flds = cfg.read_index_settings(index_name)['mappings']['properties']
        output_fields = [f for f in ind_flds if ind_flds[f]['type'] != 'dense_vector']
    search_query = {
                    "query": {
                        "match": {
                            search_field: search_term
                        }
                    },
                    "_source": output_fields,
                    "size": size,  # Adjust the number of documents to retrieve
                    
                }

    es_results = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        score = hit['_score']
        if score and score >= min_score:
            result_docs.append((score, hit['_source']))

    return result_docs


def knn_vector_search(search_term: str, search_field: str, index_name: str, output_fields: List[str] = None,
                      min_score: float = None, number_of_docs: int = 5):
    model = get_st_model()
    vector = model.encode(search_term)
    knn = {
        "field": search_field,
        "query_vector": vector,
        "k": number_of_docs,
        "num_candidates": 10000,
        "filter": {
            "term": {
                "chat_id": cfg.telegram_group_id
            }
        }
    }
   
    if not output_fields:
        ind_flds = cfg.read_index_settings(index_name)['mappings']['properties']
        output_fields = [f for f in ind_flds
                         if ind_flds[f]['type'] != 'dense_vector']
    search_query = {
        "knn": knn,
        "_source": output_fields
    }

    es_results = es_client.search(index=index_name, body=search_query)
    result_docs = [{'doc': hit['_source'], 'score': hit['_score']}
                   for hit in es_results['hits']['hits']
                   if not min_score or hit['_score'] > min_score]
    return result_docs


def get_messages_by_id(chat_id: int, msg_ids: List[int]) -> List[TelegaMessage]:
    size = len(msg_ids)  # To retrieve exactly the number of messages in msg_ids
    query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "msg_id": msg_ids  # Filter by msg_id values
                            }
                        },
                        {
                            "term": {
                                "chat_id": chat_id  # Filter by specific chat_id
                            }
                        }
                    ]
                }
            },
            "size": size  # Specify the number of results to return
        }

    es_results = es_client.search(index=cfg.index_name_messages, body=query)

    tms = [TelegaMessage.model_validate(x['_source']) for x  in es_results['hits']['hits'] ]
    return tms

