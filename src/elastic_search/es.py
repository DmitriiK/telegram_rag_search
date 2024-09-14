import json
from typing import Iterable, Dict, List
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

import src.config as cfg
from src.data_classes import TelegaMessage

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
    vector_flds = [f for f in ind_flds if ind_flds[f]['type']=='dense_vector']
    if vector_flds:
        model = get_st_model()
    for d in tqdm(docs):
        d['chat_id'] = cfg.telegram_group_id
        for ftv in vector_flds:
            fld_to_encode = ftv[0: len(ftv)- len ('_vector')] # lets rely on this convention
            if fld_to_encode in d:
                d[ftv] = model.encode(d[fld_to_encode]).tolist()
        es_client.index(index=index_name, document=d)


def simple_search(search_term: str, search_field: str, index_name: str, output_fields: List[str] = None, min_score: float = 0.7):   
    if not output_fields:
        ind_flds = cfg.read_index_settings(index_name)['mappings']['properties']
        output_fields = [f for f in ind_flds if ind_flds[f]['type'] != 'dense_vector']
    search_query = {
                    "query": {
                        "match": {
                            search_field: search_term
                        }
                    },
                    "_source": output_fields
                    }

    es_results = es_client.search(index=index_name, body=search_query)
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        score = hit['_score']
        if score >= min_score:
            result_docs.append((score, hit['_source']))

    return result_docs


def knn_vector_search(search_term: str, search_field: str, index_name: str, output_fields: List[str] = None, min_score: float = 0.7):
    model = get_st_model()
    vector = model.encode(search_term)
    knn = {
        "field": search_field,
        "query_vector": vector,
        "k": 5,
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
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        score = hit['_score']
        if score >= min_score:
            result_docs.append((score, hit['_source']))

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

