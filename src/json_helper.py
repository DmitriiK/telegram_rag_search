
import os
import json
import glob
import re

from tqdm import tqdm

import src.config as cfg
from src.read_telega_dump import telega_dump_parse_essential


def clean_json_str(json_str: str):
    json_str = re.sub('"reply_to_msg_id":\s?\d+', '', json_str)    
    # Remove trailing commas before closing brackets       
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
    return json_str 


def merge_chunks(search_folder: str):
    merged_data = []
    dump_path = cfg.messages_dump_path
    msgs = telega_dump_parse_essential(dump_path=dump_path) 
    msgs_d = {x.msg_id: x for x in msgs}
    msg_ids = set()

    for filename in glob.glob(os.path.join(search_folder, 'messages*.json')):
        print(f'parsing file name {filename}')
        with open(filename, 'r', encoding='utf-8') as file:
            json_str = file.read()
            json_str = clean_json_str(json_str)
            data = json.loads(json_str)
            #data = json.load(file)
            cnt = 0
            for tr_msg in tqdm(data): #  translated messages
                cnt += 1
                msg_id = tr_msg['msg_id']
                if msg_id in msg_ids: # we did ovelapping chuks of messages
                    break
                msg_ids.add(msg_id)
                same_msg = msgs_d.get(msg_id)
                if not same_msg:
                    print(f'msg_id {msg_id} not found in dump, something is wrong')
                    continue
                if same_msg.reply_to_msg_id:
                    tr_msg['reply_to_msg_id'] = same_msg.reply_to_msg_id
                tr_msg['user_id'] = same_msg.user_id
                merged_data.append(tr_msg)
            
    merged_data.sort(key=lambda x: int(x['msg_id']))
    return merged_data


