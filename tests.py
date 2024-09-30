from unittest import TestCase
from datetime import datetime
import json
import logging


import pyclip

from src.data_classes import TelegaMessage, date_to_json_serialize
from src.telegram_messages_index import TelegaMessageIndex
from src.read_telega_dump import telega_dump_parse_essential
from src.elastic_search import es
import src.config as cfg
from src.rag_integration import RaguDuDu

logging.getLogger().setLevel(logging.INFO)


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
        msgs = [TelegaMessage(msg_id=1, reply_to_msg_id=None, msg_date=datetime(2020, 1, 1), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=3, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name='xx', user_id='ss'),
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

        chain = mi.get_messages_tree(4, take_in_direct_relatives=True)
        ids = [x.msg_id for x in chain]
        print(ids)
        assert ids == [2, 3, 4, 5, 7]

    def test_family_adding(self):
        self.set_up_tmi()
        mi = self.telegram_index
        topic_starting_message = 189845
        # 190963  # santehnik # 186989 # rent prices 187347 # taxi in Antalia, 189845 how to feed pets
        msgs_to_feed = mi.get_potential_topic(topic_starting_message, max_steps_up=1, max_depth_down=100)
        print(msgs_to_feed[0:5])
        dls = [msg.to_dict() for msg in msgs_to_feed]
        json_string = json.dumps(dls, default=date_to_json_serialize,  ensure_ascii=False, indent=4)
        print(f'len str ={len(json_string)}')
        pyclip.copy(json_string)  # copy to clipboard for feeding to LLM

    def test_find_long_topic(self):
        self.set_up_tmi()
        mi = self.telegram_index
        topics = [(k, len(v)) for k, v in mi.topics.items() if 20 > len(v) > 10]
        topics.sort(key=lambda x: x[1], reverse=True)
        print(f'buyuk topics: {[x[0] for x in topics]}')


class TestJSONhelper(TestCase):
    def test_merge_translated(self):
        import json
        from src.json_helper import merge_chunks
        from src.data_classes import date_to_json_serialize

        search_folder = 'output/llm_output'
        out_file_path = f'{search_folder}/merged_messages.json'
        merged_data = merge_chunks(search_folder)
        with open(out_file_path, 'w') as outfile:
            json.dump(merged_data, outfile,  indent=4, default=date_to_json_serialize,  ensure_ascii=False)
        merged_data = None
                

class TestES(TestCase):

    def test_messages_eng_index(self):
        doc_file = "output/llm_output/merged_messages.json"
        es.index_json_file(doc_file, cfg.index_name_messages_eng)

    def test_topics_index(self):
        topics_path = cfg.topics_path
        es.index_json_file(topics_path, cfg.index_name_topics)

    def test_messages_index(self):
        es.load_messages_from_dump()

    def test_knn_vector_search(self):
        search_term, search_field = 'Cats feeding', 'topic_name_eng_vector'
        ret = es.knn_vector_search(search_term=search_term,  index_name=cfg.index_name_topics, search_field=search_field)
        assert ret
        score, doc = ret[0][0], ret[0][1]
        print(f'{score=}')
        ret = es.get_messages_by_id(chat_id=doc['chat_id'],  msg_ids=doc['msg_ids'])

    def test_knn_vector_search_messages_eng(self):
        search_term, search_field = 'refrigerator repair', 'msg_text_vector'
        ret = es.knn_vector_search(search_term=search_term,  index_name=cfg.index_name_messages_eng, search_field=search_field, number_of_docs=5)
        assert ret
        for score, doc in ret:    
            print(f'{score=}')
            ret = es.get_messages_by_id(chat_id=doc['chat_id'],  msg_ids=[doc['msg_id']])
            print(doc)
            print(ret)

    def test_simple_search(self):
        search_field = 'msg_text'
        tags = 'кот жрет'
        srs = es.simple_search(search_term=tags, index_name=cfg.index_name_messages, search_field=search_field, min_score=1)
        print(f'number of messages found {len(srs)}')
        srs = [{**d, "score": score} for score, d in srs]
        srs.sort(key=lambda x: x['msg_id'])
        print(srs)


class TestLLM(TestCase):

    def setUp(self):
        self.rg = RaguDuDu()

    def test_rag_by_topics(self):
        question = 'I have a Thai cat. How should I feed him? '
        ret = self.rg.rag_by_topics(question=question)
        print(ret)

    def test_rag_by_simple_search(self):
        ret = self.rg.rag_by_simple_search(question='I have a Thai cat. How should I feed him?', tags='Кот кормить')
        print(ret)

    def test_rag_by_dense_vector_search(self):
        ret = self.rg.rag_by_dense_vector_search(question='Where I can repair my refrigerator')
        print(ret)

    def test_summarize_to_topic(self):
        # 190963  # santehnik # 186989 # rent prices 187347 # taxi in Antalia, 189845 how to feed pets
        big_topic_ids = [186659, 188347, 192255, 183632, 183784, 184130, 185322, 186146, 188530, 185092, 185203, 188007, 188443, 188990, 189215, 190869, 184485, 185701, 185904, 187543, 188423, 189237, 189533, 189876, 190215, 192283, 183759, 183870, 185139, 186638, 188593, 191508, 191667, 191934, 192022, 183990, 183998, 185482, 186488, 186509, 187131, 188807, 189993, 191081, 191121, 191140, 192074, 192108, 183576, 184094, 184278, 146145, 185277, 185515, 186163, 186267, 186691, 187347, 187670, 188309, 188606, 189093, 190004, 190161, 190496, 190612, 191780, 191784, 192003, 192198, 183588, 183929, 184387, 184419, 184897, 185125, 185531, 185606, 186108, 186560, 187252, 187324, 187634, 188488, 188834, 189738, 190206, 190468, 190577, 191253, 191342]
        tdicts = []
        for tid in big_topic_ids:
            ret = self.rg.get_topic_summary_by_message(topic_message_id=tid)
            tdicts.append(json.loads(ret))    
            pyclip.copy(str(tdicts))
            with open('output/llm_output/topics.json', 'w') as fl:
                json.dump(tdicts, fl, ensure_ascii=False, indent=4)

    def test_summarize_to_topic_and_write_to_es(self):
        json_ret = self.rg.get_topic_summary_by_message(topic_message_id=189845)
        print(json_ret)
        topic_doc = json.loads(json_ret)
        es.index_docs(docs=[topic_doc], index_name=cfg.index_name_topics, recreate_index=False)
    
    def test_translate_to_english(self):
        from src.rag_integration import translate_messages
        dump_path = cfg.messages_dump_path
        msgs = telega_dump_parse_essential(dump_path=dump_path) # return iterator, not list
        max_tokens_count = 8000 * 1.5
        # gpt-4o mini; mulitpying to approx coef to be sure we can fit to context window and does not exeed number of max output tokens  
        translate_messages(msgs, "output/llm_output", max_tokens_count=max_tokens_count, overlapping_msgs_cnt=2)
