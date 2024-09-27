import logging
from tqdm import tqdm
import json

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

    def get_topic_summary_by_message(self, topic_message_id: int) -> str:
        msgs_to_feed = self.telegram_index.get_potential_topic(topic_message_id, max_steps_up=1)
        prompt = llm.build_summarization_prompt(chat_description=cfg.chat_description, messages=msgs_to_feed)
        logging.info(f'len of prompt {len(prompt)}')
        answer = llm.ask_llm(prompt)
        answer = answer.replace('```json', '').replace('```', '')
        return answer

    def rag_by_topics(self, question: str) -> str:
        search_field = 'topic_name_eng_vector'
        ret = es.knn_vector_search(search_term=question, index_name=cfg.index_name_topics, search_field=search_field)
        if ret:
            score, doc = ret[0][0], ret[0][1]
            logging.info(f'got result of knn search {score=}')
            msgs = es.get_messages_by_id(chat_id=doc['chat_id'],  msg_ids=doc['msg_ids'])
            prompt = llm.build_rag_prompt(question, chat_description=cfg.chat_description, messages=msgs)
            logging.info(prompt)
            answer = llm.ask_llm(prompt)
            return answer

    def rag_by_messages(self, question: str, tags: str = None) -> str:
        search_field = 'msg_text'
        ed_lst = es.simple_search(search_term=tags, index_name=cfg.index_name_messages, search_field=search_field, size=30, min_score=5)
        logging.info(f'got {len(ed_lst)} documents from ES')
        msgs = [TelegaMessage(**md[1]) for md in ed_lst]
        topic_msgs_all = []
        for msg in msgs:
            tms = self.telegram_index.get_potential_topic(msg.msg_id, max_depth_down=1, max_steps_up=1, take_in_direct_relatives=False)
            tms = [x for x in tms if x.msg_id not in [x.msg_id for x in topic_msgs_all]]
            topic_msgs_all.extend(tms)
        prompt = llm.build_rag_prompt(question, chat_description=cfg.chat_description, messages=topic_msgs_all)
        logging.info(f'len of prompt {len(prompt)} for {len(topic_msgs_all)} messages')
        answer = llm.ask_llm(prompt)
        return answer


def translate_messages(msgs, max_tokens_count: int = 16000):
    def output_chunk(chunk_messages):
        json_str = json.dumps(chunk_messages, indent=4, ensure_ascii=False) 

        # put breakpoint her to copy result to llm interface manually  
        print(f'chunk is ready for msgs: {chunk_min_msg_id}-{msg.msg_id}, {chunk_tokens_count=}') 
        prompt = llm.build_translation_prompt(json_str)
        ret_llm = llm.ask_llm(prompt=prompt)
        # ret_llm = llm.get_pure_json_from_llm_result(ret_llm)
        out_fn = f'output/llm_output/messages{chunk_min_msg_id}-{msg.msg_id}.json'
        with open(out_fn, "w") as outfile:
            outfile.write(ret_llm)
            print(f'data written to {out_fn}')
    chunk_messages, chunk_tokens_count, chunk_min_msg_id = [], 0, None
    letters_per_token = 2  # &?
    for msg in msgs:
        if not chunk_min_msg_id:
            chunk_min_msg_id = msg.msg_id
        msg_dic = {'msg_id': msg.msg_id, 'user_name': msg.user_name, 'msg_text': msg.msg_text}
        if msg.reply_to_msg_id:
            msg_dic['reply_to_msg_id'] = msg.reply_to_msg_id
        apr_tokens_count = len(str(msg_dic))/letters_per_token  # approximate tokens count
        if (chunk_tokens_count + apr_tokens_count) > max_tokens_count:
            output_chunk(chunk_messages)
            chunk_messages, chunk_tokens_count, chunk_min_msg_id = [], 0, None
        chunk_messages.append(msg_dic)
        chunk_tokens_count += apr_tokens_count
    if chunk_messages:   
        output_chunk(chunk_messages)