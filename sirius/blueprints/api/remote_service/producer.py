#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import os
from sirius.app import app
from sirius.blueprints.monitor.exception import InternalError
from sirius.lib.message import Message
from sirius.lib.celery_tasks import local_task, remote_task, sync_local_task


class RemoteProducer(object):
    main_queues = app.config['main_queues']
    main_queue_name = main_queues['risar_main']

    def send(self, msg, async=True):
        assert isinstance(msg, Message)
        # todo: на время тестирования без обработки исключений
        if os.environ.get('TESTING') == '1' and not app.config['SERVER']:
            async = False
        res = None
        if msg.is_to_local:
            args = (msg,)
            if async:
                local_task.apply_async(args=args, queue=self.main_queue_name)
            else:
                res = sync_local_task(*args)
        else:
            raise InternalError('Unexpected message direct')
        return res
