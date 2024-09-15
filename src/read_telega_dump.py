
# %%
import datetime
from typing import Iterable, Dict
from tqdm import tqdm
import pandas as pd
import ijson

from src.data_classes import TelegaMessage
from src.config import telegram_group_id


def telega_dump_to_pandas(dump_path: str) -> pd.DataFrame:
    msgs = telega_dump_parse_essential(dump_path)
    dd = (msg.model_dump for msg in msgs)
    df = pd.DataFrame.from_dict(dd)
    return df


def telega_dump_parse_raw_docs(dump_path: str) -> Iterable[Dict]:
    with open(dump_path, "rb") as f:
        msgs = (msg for msg in ijson.items(f, 'messages.item')
                if msg['type'] != 'service')
        for raw_msg in msgs:
            yield raw_msg


def telega_dump_parse_essential(dump_path: str) -> Iterable[TelegaMessage]:
    raw_docs = telega_dump_parse_raw_docs(dump_path)
    for raw_msg in tqdm(raw_docs):
        tm = __extract_message_data(raw_msg)
        yield tm


def __extract_message_data(msg) -> TelegaMessage:
    tes = msg.get('text_entities')
    text = ''.join([mp['text'] for mp in tes]) if tes else ''
    tm = TelegaMessage(msg_id=msg["id"],
                       msg_date=datetime.datetime.strptime(msg['date'], "%Y-%m-%dT%H:%M:%S"),
                       user_id=msg.get('from_id'),
                       user_name=msg.get('from'),
                       reply_to_msg_id=msg.get('reply_to_message_id'),
                       msg_text=text,
                       chat_id=telegram_group_id
                      )
    return tm


    

# %%df

# %%
