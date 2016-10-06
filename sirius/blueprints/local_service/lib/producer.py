#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
import os
from sirius.blueprints.local_service.lib.client.request import request_by_url
from sirius.celery_queue import remote_queue_name_list, main_queue_name
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from sirius.lib.celery_tasks import local_task, remote_task
from sirius.lib.remote_system import remote_system


class LocalProducer(object):
    def send(self, msg):
        assert isinstance(msg, Message)

        if msg.is_to_local:
            local_task.apply_async(args=(msg,), queue=main_queue_name)
        elif msg.is_to_remote:
            if msg.is_send_data:
                implement = Implementation()
                for queue_name in remote_queue_name_list:
                    rmt_sys_code = remote_system.get_code(queue_name)
                    reformer = implement.get_reformer(rmt_sys_code)
                    missing_requests = reformer.get_local_missing_requests(msg)
                    miss_data = self.request_data(missing_requests)
                    msg.add_missing_data(miss_data)
                    # todo: на время тестирования без обработки исключений
                    if os.environ['TESTING'] == '1':
                        remote_task(msg, rmt_sys_code)
                    else:
                        remote_task.apply_async(args=(msg, rmt_sys_code),
                                                queue=queue_name)
            elif msg.is_send_event:
                rmt_sys_code = remote_system.get_event_system_code()
                remote_task(msg, rmt_sys_code)
            elif msg.is_request:
                # todo: rmt_sys_code
                rmt_sys_code = remote_system.get_system_code(msg)
                remote_task(msg, rmt_sys_code)
            elif msg.is_result:
                rmt_sys_code = msg.get_header().meta['remote_system_code']
                remote_task(msg, rmt_sys_code)
            else:
                raise Exception('Unexpected message type')
        else:
            raise Exception('Message direct missing')
        return True

    def request_data(self, missing_requests):
        res = []
        local_data = None
        # todo: цикл вложенных дозапросов и связывание ответов
        for miss_req in missing_requests:
            miss_req.link_miss_requests(local_data)
            local_data = request_by_url(miss_req.method, miss_req.url, None)
            res.append(local_data)
        return res
