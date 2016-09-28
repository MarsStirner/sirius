#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.extensions import celery


@celery.task
def local_task(msg):
    from sirius.blueprints.local_service.lib.consumer import LocalConsumer
    receiver = LocalConsumer()
    receiver.process(msg)


@celery.task
def remote_task(msg, rmt_sys_code):
    from sirius.blueprints.remote_service.lib.consumer import RemoteConsumer
    receiver = RemoteConsumer()
    receiver.process(msg, rmt_sys_code)


@celery.task
def scheduler_task():
    from sirius.blueprints.remote_service.lib.scheduler import Scheduler
    scheduler = Scheduler()
    scheduler.execute()
