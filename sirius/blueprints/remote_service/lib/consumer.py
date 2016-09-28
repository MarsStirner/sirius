#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.remote_service.lib.implement import Implementation
from sirius.blueprints.remote_service.lib.producer import RemoteProducer
from sirius.blueprints.remote_service.lib.result import OperationResult
from sirius.blueprints.remote_service.lib.store import DataStore
from sirius.lib.message import Message
from sirius.lib.remote_system import remote_system


class RemoteConsumer(object):
    def process(self, msg, rmt_sys_code):
        assert isinstance(msg, Message)
        res = True
        implement = Implementation()
        reformer = implement.get_reformer(rmt_sys_code)
        transfer = implement.get_transfer(rmt_sys_code)

        # сценарий обработки сообщения
        if msg.is_to_remote:
            if remote_system.is_passive(rmt_sys_code):
                if msg.is_send_data:
                    remote_reformed_data = reformer.to_remote(msg)
                    trans_res = transfer.execute(remote_reformed_data)
                    reformer.remote_conformity(msg, trans_res)
                    hdr = msg.get_header()
                    op_res = OperationResult()
                    next_msg = op_res.check(hdr.method, hdr.url)
                    if next_msg:
                        producer = RemoteProducer()
                        producer.send(next_msg, async=False)
                elif msg.is_send_event:
                    remote_reformed_data = reformer.to_remote(msg)
                    trans_res = transfer.execute(remote_reformed_data)
                    reformer.remote_conformity(msg, trans_res)
                elif msg.is_result:
                    remote_data = msg.get_source_data()
                    reformer.local_conformity(remote_data, msg)
                else:
                    raise Exception('Unexpected message type')
            elif remote_system.is_active(rmt_sys_code):
                if msg.is_send_data:
                    remote_reformed_data = reformer.to_remote(msg)
                    data_store = DataStore()
                    data_store.place(remote_reformed_data)
                    data_store.commit_all_changes()
                elif msg.is_result:
                    remote_data = msg.get_source_data()
                    reformer.local_conformity(remote_data, msg)
                else:
                    raise Exception('Unexpected message type')
            else:
                raise Exception('Type of remote system is not define')
        elif msg.is_to_local:
            raise Exception('Wrong message direct')
        else:
            raise Exception('Message direct is not define')
        return res
