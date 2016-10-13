#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
import traceback

import sys

from sirius.extensions import celery
from sirius.blueprints.scheduler.api import Scheduler


@celery.task
def local_task(msg):
    from sirius.blueprints.api.local_service.consumer import LocalConsumer
    receiver = LocalConsumer()
    try:
        res = receiver.process(msg)
    except Exception as exc:
        traceback.print_exc()
        # j, code, headers = jsonify_api_exception(e, traceback.extract_tb(sys.exc_info()[2]))
        raise
    return res


@celery.task
def remote_task(msg, rmt_sys_code):
    from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
    receiver = RemoteConsumer()
    receiver.process(msg, rmt_sys_code)


@celery.task
def scheduler_task():
    scheduler = Scheduler()
    scheduler.execute()
