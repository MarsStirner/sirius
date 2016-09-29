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

        # сценарий обработки сообщения
        if msg.is_to_remote:
            if remote_system.is_passive(rmt_sys_code):
                if msg.is_send_data:
                    miss_req_msgs = reformer.get_missing_requests(msg)
                    miss_data_msgs = self.send_msgs(miss_req_msgs)
                    reformer.to_remote(msg, miss_data_msgs)
                    hdr = msg.get_header()
                    op_res = OperationResult()
                    result_msg = op_res.check(hdr.method, hdr.url)
                    if result_msg:
                        self.send_msgs([result_msg])
                elif msg.is_send_event:
                    reformer.to_remote(msg)
                elif msg.is_result:
                    remote_data = msg.get_source_data()
                    reformer.local_conformity(remote_data, msg)
                else:
                    raise Exception('Unexpected message type')
            elif remote_system.is_active(rmt_sys_code):
                if msg.is_send_data:
                    remote_reformed_data = reformer.get_reformed_data(msg)
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

    def send_msgs(self, msgs, async=False):
        producer = RemoteProducer()
        res = [producer.send(msg, async=async) for msg in msgs]
        return res
