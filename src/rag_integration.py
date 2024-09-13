
from typing import List
import logging
from tqdm import tqdm

import src.config as cfg
from src.data_classes import TelegaMessage
from src.telegram_messages_index import TelegaMessageIndex
from src.read_telega_dump import telega_dump_parse_essential
import src.elastic_search.es as es
import src.llm as llm


class RaguDuDu:
    def __init__(self):
        print("Creating the messages    index...")
        dump_path = cfg.messages_dump_path
        msgs = telega_dump_parse_essential(dump_path=dump_path)
        # this supposed to be loaded from es index. todo
        mi = TelegaMessageIndex()
        for msg in tqdm(msgs):
            mi.add_item(msg)
        self.telegram_index = mi

    def rag_by_topics(self, question: str) -> str:
        search_field = 'topic_name_eng_vector'
        ret = es.knn_vector_search(search_term=question, index_name=cfg.index_name_topics, search_field=search_field)
        if ret:
            score, doc = ret[0][0], ret[0][1]
            logging.info(f'got result of knn search {score=}')
            msgs = es.get_messages_by_id(chat_id=doc['chat_id'],  msg_ids=doc['msg_ids'])
            prompt = llm.build_rag_prompt(question, chat_desciption=cfg.chat_desciption, messages=msgs)
            logging.info(prompt)
            answer = llm(prompt)
            return answer

    def rag_by_messages(self, tags: str, question: str = None) -> str:
        search_field = 'msg_text'
        ed_lst = es.simple_search(search_term=tags, index_name=cfg.index_name_messages, search_field=search_field)
        msgs = [TelegaMessage(**md[1]) for md in ed_lst]
        topic_msgs_all = []
        for msg in msgs:
            tms = self.telegram_index.get_potential_topic(msg.msg_id)
            tms = [x for x in tms if x.msgs_id not in [x.msg_id for x in topic_msgs_all]]
            topic_msgs_all.append(tms)
        return topic_msgs_all
