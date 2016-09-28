#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.celery_queue import remote_queue_name_list, main_queue_name
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
                for queue_name in remote_queue_name_list:
                    rmt_sys_code = remote_system.get_code(queue_name)
                    remote_task.apply_async(args=(msg, rmt_sys_code),
                                            queue=queue_name)
            elif msg.is_send_event:
                rmt_sys_code = remote_system.get_event_system_code()
                remote_task(msg, rmt_sys_code)
            else:
                raise Exception('Unexpected message type')
        else:
            raise Exception('Message direct missing')
        return True
