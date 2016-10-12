#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.lib.implement import Implementation
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
                    reformed_data = reformer.reform_msg(msg)
                    reformer.transfer__send_data(reformed_data)
                    hdr = msg.get_header()
                    op_res = OperationResult()
                    result_msg = op_res.check(hdr.method, hdr.url)
                    if result_msg:
                        self.producer_send_msgs([result_msg])
                elif msg.is_send_event:
                    reformed_data = reformer.reform_msg(msg)
                    reformer.transfer__send_data(reformed_data)
                elif msg.is_result:
                    remote_data = msg.get_source_data()
                    reformer.conformity_local(remote_data, msg)
                elif msg.is_request:
                    reformed_req = reformer.reform_req(msg)
                    entity_packages = reformer.get_entity_packages(reformed_req)
                    self.send_diff_data(entity_packages, reformer)
                else:
                    raise Exception('Unexpected message type')
            elif remote_system.is_active(rmt_sys_code):
                if msg.is_send_data:
                    # todo: не готов вариант взаимодействия с мис
                    miss_req_msgs = reformer.get_missing_requests(msg)
                    miss_data_msgs = self.producer_send_msgs(miss_req_msgs)
                    remote_reformed_data = reformer.get_reformed_data(msg, miss_data_msgs)
                    data_store = DataStore()
                    data_store.place(remote_reformed_data)
                    data_store.commit_all_changes()
                elif msg.is_result:
                    remote_data = msg.get_source_data()
                    reformer.conformity_local(remote_data, msg)
                else:
                    raise Exception('Unexpected message type')
            else:
                raise Exception('Type of remote system is not define')
        elif msg.is_to_local:
            raise Exception('Wrong message direct')
        else:
            raise Exception('Message direct is not define')
        return res

    def producer_send_msgs(self, msgs, async=False):
        producer = RemoteProducer()
        res = [producer.send(msg, async=async) for msg in msgs]
        return res

    def send_diff_data(self, entity_packages, reformer):
        # data_store = DataStore()
        # data_store.check_diffs(entity_packages)
        # data_store.save_all_changes()
        msgs = reformer.create_remote_messages(entity_packages)
        self.producer_send_msgs(msgs)
        # data_store.commit_all_changes()
