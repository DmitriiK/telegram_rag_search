
from typing import List
from collections import defaultdict
import logging

import src.config as cfg
from src.data_classes import TelegaMessage

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
        return self.msdg_ids.get(msg_id)

    def get_parent_messages(self, msg_id: int) -> List[TelegaMessage]:
        ret_lst = []
        msg = self.msdg_ids.get(msg_id)
        while msg and msg.reply_to_msg_id:
            reply_to_msg_id = msg.reply_to_msg_id
            msg =self.get_message(reply_to_msg_id)
            if not msg:
                logging.warn(f'inconsistent data in index for reply_to_msg_id: {reply_to_msg_id}')
            else:
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

    def get_messages_tree(self, msg_id: int) -> List[TelegaMessage]:
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
    
    
    def get_family_candidates(self, family: List[TelegaMessage]):
        nm_td  = cfg.near_messages_time_delta
        nm_nm = cfg.near_messages_number_of_messages_delta
        family_ids = {x.msg_id for x in family}
        family.sort(key=lambda x: x.msg_id)
        family_candidates = []

        for i, m in enumerate(family):
            dt_interval = (m.msg_date - nm_td,  m.msg_date + nm_td)
            next_family_msg_id = family[i+1].msg_id if i < len(family) - 1 else None 
            prev__family_msg_id = family[i-1].msg_id if i > 0 else 0
            msgs_interval = max(m.msg_id - nm_nm - 1, prev__family_msg_id), min(m.msg_id + nm_nm + 1, next_family_msg_id if next_family_msg_id else m.msg_id + nm_nm)
            # as family candidates we are considering the messages some time before and after every explicit member of family
            for _, msg_ids in filter(lambda itm: dt_interval[0] <= itm[0] <= dt_interval[1], self.msg_date_ids.items()):
                for msg_id in filter(lambda msg_id: msgs_interval[0] < msg_id < msgs_interval[1] and msg_id not in family_ids, msg_ids):
                    new_msg = self.msdg_ids[msg_id]
                    if new_msg not in family_candidates: # need to sort out why it happens
                        family_candidates.append(new_msg)
        return family_candidates
    
    def get_potential_topic(self, topic_starting_message: int)-> List[TelegaMessage]:
            topic_msgs = self.get_messages_tree(topic_starting_message)
            fc = self.get_family_candidates(topic_msgs) # calculation of family candidates
            msgs_to_feed = [(m, True) for m in topic_msgs] + [(m, False) for m in fc]
            msgs_to_feed.sort(key = lambda x: x[0].msg_date)
            return msgs_to_feed

               

                                            



    
