import datetime
from pydantic import BaseModel, Field
from typing import Optional, List
from collections import defaultdict
class TelegaMessage(BaseModel):
    msg_id:   int = Field(description='Telegram message id, unique for particular chat or group')
    msg_date: datetime.datetime = Field(description='date of message creation')
    user_name: Optional[str] = Field(description='User full name for my chat')
    user_id: Optional[str] = Field(description='user id')
    reply_to_msg_id: Optional[int] = Field(description='reference to the message, this is respondint to')
    msg_text: Optional[str] = Field (description='text of the message')


class TelegaMessageIndex:
    def __init__(self):
        self.msdg_ids = dict() # Dict[int, TelegaMessage]
        self.reply_to_msg_ids= defaultdict(set) # Dict[int, Set[int]] # set of child messages ids
        self.msg_date_ids = defaultdict(set) # Dict[int, Set[int]] # set of child messages ids

    def add_item(self, msg: TelegaMessage):
        if msg.msg_id not in self.msdg_ids: # i assume no need to clear data if item already in the index 
            self.msdg_ids[msg.msg_id] = msg
            if msg.reply_to_msg_id:
                self.reply_to_msg_ids[msg.reply_to_msg_id].add(msg.msg_id)
            self.msg_date_ids[msg.msg_date].add(msg.msg_id)

    def get_message(self, msg_id: int)->TelegaMessage: 
        return self.msdg_ids[msg_id]

    def get_parent_messages(self, msg_id: int) -> List[TelegaMessage]:
        ret_lst = []
        msg = self.msdg_ids.get(msg_id)
        while msg.reply_to_msg_id:
            msg =self.get_message(msg.reply_to_msg_id)
            if not msg:
                raise Exception(f'inconsistent data in index for reply_to_msg_id: {msg.reply_to_msg_id}')
            ret_lst.append(msg)
        return ret_lst  
        
    def get_children_messages(self, msg_id: int) -> List[TelegaMessage]:
        descendants = [] 
        def dfs(parent_msg_id: int):
            for id in self.reply_to_msg_ids[parent_msg_id]:
                msg =self.get_message(id)
                if not msg:
                    raise Exception(f'inconsistent data in index for id: {id}')
                descendants.append(msg)
                dfs(id)
        dfs(msg_id)
        return descendants

    def get_messages_tree(self, msg_id: int):
        msg = self.msdg_ids.get(msg_id)
        ancestors =self.get_parent_messages(msg_id)[::-1] # reverting of order of list, topmost first
        descendants = self.get_children_messages(msg_id)
        direct_relatives = ancestors + [msg] +descendants
        drids = {x.msg_id for x  in direct_relatives}
        in_direct_relatives = [] # aunts, nephews, etc
        for anc in ancestors:
            rr = [r for r in self.get_children_messages(anc.msg_id) if r.msg_id not in drids]
            in_direct_relatives.extend(rr)
        family =  direct_relatives+ in_direct_relatives
        family.sort(key=lambda x: x.msg_id)
        return family





    
