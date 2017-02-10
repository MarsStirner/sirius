#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.monitor.exception import InternalError, LoggedException
from sirius.lib.implement import Implementation
from sirius.blueprints.api.remote_service.producer import RemoteProducer
from sirius.blueprints.api.remote_service.lib.result import OperationResult
from sirius.blueprints.difference.api import Difference
from sirius.lib.message import Message
from sirius.lib.remote_system import remote_system
from sirius.models.operation import OperationCode


class RemoteConsumer(object):
    def process(self, msg, rmt_sys_code):
        assert isinstance(msg, Message)
        res = True
        implement = Implementation()
        reformer = implement.get_reformer(rmt_sys_code, msg.get_stream_id())

        # сценарий обработки сообщения
        if msg.is_to_remote:
            if msg.is_send_data:
                if remote_system.is_passive(rmt_sys_code):
                    reformed_data = reformer.reform_msg(msg)
                    reformer.send_to_remote_data(reformed_data)
                    hdr = msg.get_header()
                    op_res = OperationResult(msg.stream_id)
                    result_msg = op_res.check(hdr.method, hdr.url)
                    if result_msg:
                        self.producer_send_msgs([result_msg])
                elif remote_system.is_active(rmt_sys_code):
                    # todo: не готов вариант взаимодействия с мис
                    miss_req_msgs = reformer.get_missing_requests(msg)
                    miss_data_msgs = self.producer_send_msgs(miss_req_msgs)
                    remote_reformed_data = reformer.get_reformed_data(msg, miss_data_msgs)
                    data_store = Difference()
                    data_store.place(remote_reformed_data)
                    data_store.commit_all_changes()
                else:
                    raise InternalError(
                        'Type of remote system is not define: %s' % rmt_sys_code
                    )
            elif msg.is_send_event:
                reformed_data = reformer.reform_msg(msg)
                res = reformer.send_to_remote_data(reformed_data)
            elif msg.is_result:
                remote_data = msg.get_source_data()
                reformer.conformity_local(remote_data, msg)
            elif msg.is_request:
                reformed_req = reformer.reform_req(msg)
                entity_package = reformer.get_entity_package_by_req(reformed_req)
                self.send_diff_data(entity_package, reformer, msg)
            else:
                raise InternalError('Unexpected message type')
        elif msg.is_to_local:
            raise InternalError('Wrong message direct')
        else:
            raise InternalError('Message direct is not define')
        return res

    def producer_send_msgs(self, msgs, async=False, skip_err=False, callback=None):
        producer = RemoteProducer()
        if callback:
            res = []
            for msg in msgs:
                try:
                    r = producer.send(msg, async=async)
                    res.append(r)
                    if callable(callback):
                        callback(msg)
                except LoggedException:
                    if not skip_err:
                        raise
        else:
            res = [producer.send(msg, async=async) for msg in msgs]
        return res

    def send_diff_data(self, entity_package, reformer, msg):
        diff = Difference()
        diff_entity_packages = diff.mark_diffs(entity_package)
        # diff.save_all_changes()
        msgs = reformer.create_to_local_messages(diff_entity_packages)
        skip_err = msg.get_header().meta['local_operation_code'] == OperationCode.READ_MANY
        self.producer_send_msgs(msgs, skip_err=skip_err, callback=diff.save_change)
        diff.commit_all_changes()
