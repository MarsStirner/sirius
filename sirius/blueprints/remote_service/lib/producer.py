#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.lib.message import Message
from sirius.lib.celery_tasks import local_task, remote_task
from sirius.celery_queue import remote_queue_name_list, main_queue_name


class RemoteProducer(object):
    def send(self, msg, async=True):
        assert isinstance(msg, Message)
        res = None
        if msg.is_to_local:
            args = (msg,)
            if async:
                local_task.apply_async(args=args, queue=main_queue_name)
            else:
                res = local_task(*args)
        else:
            raise Exception('Unexpected message direct')
        return res
