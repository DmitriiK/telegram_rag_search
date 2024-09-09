import json
from typing import Iterable, Dict
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch

import src.config as cfg

es_client = Elasticsearch(cfg.es_url) 

# es_client.info()

def get_st_model():
    model = SentenceTransformer(cfg.sent_tranformer_model_name)
    return model

def index_json_file(file_path: str, index_name, recreate_index = True):
    with open(file_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    index_docs(docs, index_name, recreate_index)


def index_docs(docs: Iterable[Dict], index_name, recreate_index = True):
    ind_set = cfg.read_index_settings(index_name)
    if recreate_index:
        es_client.indices.delete(index=index_name, ignore_unavailable=True)
        es_client.indices.create(index=index_name, body=ind_set)

    ind_flds = ind_set['mappings']['properties']
    vector_flds = [f for f in ind_flds if ind_flds[f]['type']=='dense_vector']
    if vector_flds:
        model = get_st_model()
    for d in docs:
        d['chat_id'] = cfg.telegram_group_id
        for ftv in vector_flds:
            fld_to_encode = ftv[0: len(ftv)- len ('_vector')] # lets rely on this convention
            if fld_to_encode in d:
                d[ftv] = model.encode(d[fld_to_encode]).tolist()
        es_client.index(index=index_name, document=d)



def elastic_search_knn(field, vector, course, index_name):
    knn = {
        "field": field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000,
        "filter": {
            "term": {
                "course": course
            }
        }
    }

    search_query = {
        "knn": knn,
        "_source": ["text", "section", "question", "course", "id"]
    }

    es_results = es_client.search(
        index=index_name,
        body=search_query
    )
    
    result_docs = []
    
    for hit in es_results['hits']['hits']:
        result_docs.append(hit['_source'])

    return result_docs

def question_text_vector_knn(q):
    question = q['question']
    course = q['course']
    model = '' # stub
    v_q = model.encode(question)

    return elastic_search_knn('question_text_vector', v_q, course)

def rag(query: dict, model='gpt-4o') -> str:
    search_results = question_text_vector_knn(query)
    prompt = '' # build_prompt(query['question'], search_results)
    answer = '' # llm(prompt, model=model)
    return answer