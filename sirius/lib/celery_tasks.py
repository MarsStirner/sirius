#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
import sys

import datetime

from celery.task import periodic_task
from sirius.blueprints.monitor.exception import task_entry, beat_entry
from sirius.extensions import celery
from sirius.blueprints.scheduler.api import Scheduler


@celery.task(bind=True, default_retry_delay=5*60, max_retries=12)
@task_entry
def local_task(self, msg):
    sync_local_task(msg, self)


def sync_local_task(msg, task=None):
    from sirius.blueprints.api.local_service.consumer import LocalConsumer
    receiver = LocalConsumer()
    res = receiver.process(msg)
    return res


@celery.task(bind=True, default_retry_delay=5*60, max_retries=12)
@task_entry
def remote_task(self, msg, rmt_sys_code):
    sync_remote_task(msg, rmt_sys_code, self)


def sync_remote_task(msg, rmt_sys_code, task=None):
    from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
    receiver = RemoteConsumer()
    res = receiver.process(msg, rmt_sys_code)
    return res


# @periodic_task(run_every=datetime.timedelta(minutes=5), queue='sir_test_celerybeat_queue')
@celery.task(bind=True)
@beat_entry
def scheduler_task(self):
    scheduler = Scheduler()
    scheduler.run()
