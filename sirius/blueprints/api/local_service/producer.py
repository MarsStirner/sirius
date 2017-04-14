#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
import os
from sirius.app import app
from sirius.blueprints.difference.api import Difference
from sirius.blueprints.monitor.exception import InternalError, LoggedException
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from sirius.lib.celery_tasks import local_back_task, remote_task, sync_remote_task
from sirius.lib.remote_system import remote_system
from sirius.models.operation import OperationCode

main_queues = app.config['main_queues']
main_queue_name = main_queues['risar_main']
back_queue_name = main_queues['risar_back']
error_1_queue_name = main_queues['risar_error_1']
error_2_queue_name = main_queues['risar_error_2']


class LocalProducer(object):
    def send(self, msg):
        assert isinstance(msg, Message)

        res = True
        if msg.is_to_local:
            # доп. очередь, т.к. основная может быть забита входящим потоком
            local_back_task.apply_async(args=(msg,), queue=back_queue_name)
        elif msg.is_to_remote:
            if msg.is_send_data:
                implement = Implementation()
                for rmt_sys_code in remote_system.get_codes():
                    for queue_name in remote_system.get_queue_names(rmt_sys_code):
                        reformer = implement.get_reformer(rmt_sys_code, msg.get_stream_id())
                        entity_package = reformer.get_entity_package_by_msg(msg)
                        self.send_diff_data(entity_package, reformer, msg, rmt_sys_code, queue_name)
            elif msg.is_send_event:
                implement = Implementation()
                rmt_sys_code = remote_system.get_event_system_code()
                reformer = implement.get_reformer(rmt_sys_code, msg.get_stream_id())
                entity_package = reformer.get_entity_package_by_msg(msg)
                msgs = reformer.create_to_remote_messages(entity_package)
                res = all(self.send_msgs(msgs, rmt_sys_code, async=False))
            elif msg.is_request:
                rmt_sys_code = msg.get_header().meta['remote_system_code']
                sync_remote_task(msg, rmt_sys_code)
            elif msg.is_result:
                rmt_sys_code = msg.get_header().meta['remote_system_code']
                sync_remote_task(msg, rmt_sys_code)
            else:
                raise InternalError('Unexpected message type')
        else:
            raise InternalError('Message direct missing')
        return res

    def send_diff_data(self, entity_packages, reformer, msg, rmt_sys_code, queue_name):
        # diff = Difference()
        # diff_entity_packages = diff.mark_diffs(entity_packages)
        # diff.save_all_changes()
        msgs = reformer.create_to_remote_messages(entity_packages)
        op_code = msg.get_header().meta['local_operation_code']
        skip_err = op_code == OperationCode.READ_MANY or not op_code and len(msgs) > 1
        # self.producer_send_msgs(msgs, skip_err=skip_err, callback=diff.save_change)
        self.send_msgs(msgs, rmt_sys_code, queue_name, skip_err=skip_err)
        # diff.commit_all_changes()

    def send_msgs(self, msgs, rmt_sys_code, queue_name=None, async=True, skip_err=False, callback=None):
        # чтобы skip_err работал
        callback = callback or True
        if callback:
            res = []
            for msg in msgs:
                try:
                    r = self.task_run(msg, rmt_sys_code, async, queue_name)
                    res.append(r)
                    if callable(callback):
                        callback(msg)
                except LoggedException:
                    if not skip_err:
                        raise
        else:
            res = [self.task_run(msg, rmt_sys_code, async, queue_name) for msg in msgs]
        return res

    def task_run(self, msg, rmt_sys_code, async, queue_name=None):
        res = None
        # todo: на время тестирования без обработки исключений
        if not async or os.environ.get('TESTING') == '1':
            res = sync_remote_task(msg, rmt_sys_code)
        else:
            remote_task.apply_async(args=(msg, rmt_sys_code),
                                    queue=queue_name)
        return res
