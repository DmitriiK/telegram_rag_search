from datetime import datetime
import json
from pydantic import BaseModel, Field
from typing import Optional, List

date_time_format = '%Y-%m-%d %H:%M:%S'


def date_to_json_serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # or obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError("Type not serializable")


class TelegaMessage(BaseModel):
    msg_id:   int = Field(description='Telegram message id, unique for particular chat or group')
    msg_date: datetime = Field(description='date of message creation')
    user_id: Optional[str] = Field(description='user id',default=None)
    user_name: Optional[str] = Field(description='User full name for my chat', default=None)
    chat_id: Optional[int] = Field(description='chat or group id', default=None)
    reply_to_msg_id: Optional[int] = Field(description='reference to the message, this is responding to')
    msg_text: Optional[str] = Field(description='text of the message')

    def __str__(self):
        return f'{self.msg_date.strftime(date_time_format)}; {self.msg_text}'

    def __repr__(self):
        return f'{self.msg_id}:{self.msg_date.strftime(date_time_format)}; {self.msg_text}'
 
    def __eq__(self, other): 
        if isinstance(other, TelegaMessage): 
            if other.msg_id == self.msg_id: 
                return True
        return False

    def __hash__(self):
        return self.msg_id
    
    def to_dict(self, is_in_family: bool = None):
        dmsg = self.model_dump()
        if is_in_family is not None:
            dmsg['is_in_family'] = is_in_family
        return dmsg


def convert_to_json_list(messages: List[TelegaMessage]):
    dss = [msg.model_dump() for msg in messages]
    json_string = json.dumps(dss, default=date_to_json_serialize, ensure_ascii=False, indent=4)
    return json_string

