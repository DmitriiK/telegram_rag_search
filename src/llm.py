from dotenv import load_dotenv
from typing import List
import logging
from openai import OpenAI

import src.config as cfg
from src.data_classes import TelegaMessage, convert_to_json_list
import  src.elastic_search.es  as es

load_dotenv()

client = OpenAI()


def llm(prompt, model=cfg.llm_model):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def build_rag_prompt(question: str, chat_desciption:str, messages: List[TelegaMessage]):
    prompt_template = """
    You will be given some data. That data is a sequence of messages from chat from some messager.
    This sequnce will be given in json format.
    This chat is devoted to {chat_desciption}.
    The question, for which you should give the answer is:
    '{question}'.

    The data that is provided for you will contain msg_id field for each message. 
    You should output the id-s for the messages, that are relevant to the question and which you use for the answer.
    The date - where you can try to find additional information to answer the quistion is:
    ---
    {messages}
    """
    msg_json = convert_to_json_list(messages)
    return prompt_template.format(question = question, chat_desciption = chat_desciption, messages=msg_json)


def rag(question: str) -> str:
    search_field = 'topic_name_eng_vector'
    chat_desciption = 'Life or russian relocants in Antalya'
    ret = es.knn_vector_search(search_term=question,index_name=cfg.index_name_topics, search_field=search_field)
    if ret:
        score, doc = ret[0][0], ret[0][1]
        logging.info(f'got result of knn search {score=}')
        msgs = es.get_messages_by_id(chat_id =  doc['chat_id'],  msg_ids=doc['msg_ids'])
        prompt = build_rag_prompt(question, chat_desciption=chat_desciption, messages=msgs)
        answer = llm(prompt)
        return answer
