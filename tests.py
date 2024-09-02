from unittest import TestCase
from datetime import datetime
from data_classes import TelegaMessage, TelegaMessageIndex

class TestTelega(TestCase):

    def test_add_to_index(self):
        msgs = [TelegaMessage(msg_id=1, reply_to_msg_id=None, msg_date=datetime(2020, 1, 1), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=3, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=1, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
                ]
        mi = TelegaMessageIndex()
        for msg in msgs:
            mi.add_item(msg)
        assert len(mi.msdg_ids)==3


    def test_parent_child_chain(self):
        msgs = [TelegaMessage(msg_id=1, reply_to_msg_id=None, msg_date=datetime(2020, 1, 1), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=2, reply_to_msg_id=None, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=3, reply_to_msg_id=2, msg_date=datetime(2020, 1, 2), msg_text='text 1', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=4, reply_to_msg_id=2, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=5, reply_to_msg_id=4, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=6, reply_to_msg_id= None, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
                TelegaMessage(msg_id=7, reply_to_msg_id=4, msg_date=datetime(2020, 1, 2), msg_text='text new', user_name ='xx', user_id='ss'),
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




TestTelega().test_parent_child_chain()



