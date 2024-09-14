from unittest import TestCase
from datetime import datetime
import json
from tqdm import tqdm

import pyclip

from src.data_classes import TelegaMessage,  date_to_json_serialize
from src.telegram_messages_index import TelegaMessageIndex
from src.read_telega_dump import telega_dump_parse_essential
from src.elastic_search import es
import src.config as cfg
from src.rag_integration import RaguDuDu


class TestTelega(TestCase):

    def set_up_tmi(self):
        # This method runs once for the entire class.
        print("Creating the messages index...")
        dump_path = cfg.messages_dump_path
        msgs = telega_dump_parse_essential(dump_path=dump_path)
        mi = TelegaMessageIndex()
        for msg in msgs:
            mi.add_item(msg)
        self.telegram_index = mi

    def test_add_to_index(self):
        msgs = [TelegaMessage(msg_id=1, reply_to_msg_id=None, msg_date=datetime(2020, 1, 1), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=3, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
                ]
        mi = TelegaMessageIndex()
        for msg in msgs:
            mi.add_item(msg)
        assert len(mi.msdg_ids) == 3

    def test_parent_child_chain(self):
        msgs = [TelegaMessage(msg_id=1, reply_to_msg_id=None, msg_date=datetime(2020, 1, 1), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=None, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=3, reply_to_msg_id=2, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=4, reply_to_msg_id=2, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=5, reply_to_msg_id=4, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=6, reply_to_msg_id=None, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=7, reply_to_msg_id=4, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name='xx', user_id='ss'),
                ]
        mi = TelegaMessageIndex()
        for msg in msgs:
            mi.add_item(msg)
        chain = mi.get_children_messages(2)
        print([x.msg_id for x in chain])
        assert [x.msg_id for x in chain] == [3, 4, 5, 7]

        chain = mi.get_parent_messages(5)
        print([x.msg_id for x in chain])
        assert [x.msg_id for x in chain] == [4, 2]

        chain = mi.get_messages_tree(4)
        print([x.msg_id for x in chain])
        assert [x.msg_id for x in chain] == [2, 3, 4, 5, 7]

    def test_family_adding(self):
        self.set_up_tmi()
        mi = self.telegram_index
        topic_starting_message = 189845  # 
        # 190963  # santehnik # 186989 # rent prices 187347 # taxi in Antalia, 189845 how to feed pets
        msgs_to_feed = mi.get_potential_topic(topic_starting_message, max_steps_up=1, max_depth_down=1) 
        print(msgs_to_feed[0:3])
        dls = [msg.to_dict(is_in_family) for msg, is_in_family in msgs_to_feed]
        json_string = json.dumps(dls, default=date_to_json_serialize,  ensure_ascii=False, indent=4)
        print(f'len str ={len(json_string)}')
        pyclip.copy(json_string)  # copy to clipboard for feeding to LLM


class TestES(TestCase):

    def test_topics_index(self):
        topics_path = cfg.topics_path
        es.index_json_file(topics_path, cfg.index_name_topics)

    def test_messages_index(self):
        messages_dump_path = cfg.messages_dump_path
        msgs = telega_dump_parse_essential(dump_path=messages_dump_path)
        subset = [msg.model_dump() for msg in msgs]
        # subset = (x for x in subset if x['msg_date']> datetime(2024,1, 1))
        # encoding = tiktoken.encoding_for_model(cfg.llm_model)
        es.index_docs(docs=subset, index_name=cfg.index_name_messages, recreate_index=True)

    def test_knn_vector_search(self):
        search_term, search_field = 'Cats feeding', 'topic_name_eng_vector'
        ret = es.knn_vector_search(search_term=search_term,index_name=cfg.index_name_topics, search_field=search_field)
        assert ret
        score, doc = ret[0][0], ret[0][1]
        print(f'{score=}')
        ret = es.get_messages_by_id(chat_id=doc['chat_id'],  msg_ids=doc['msg_ids'])


class TestLLM(TestCase):

    def setUp(self):
        self.rg = RaguDuDu()

    def test_rag_by_topics(self):
        ret = self.rg.rag_by_topics('How can I feed my cat and how much would it cost?')
        print(ret)

    def test_rag_by_messages(self):
        ret = self.rg.rag_by_messages('сантехник Влад')
        print(ret)



    




