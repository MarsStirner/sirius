#! coding:utf-8
"""


@author: BARS Group
@date: 22.09.2016

"""
from hitsl_utils.safe import safe_traverse
from kombu import Queue, Exchange
from sirius.models.system import RegionCode
from sirius.app import app

main_queues = app.config['main_queues']
main_queue_name = main_queues['risar_main']
error_1_queue_name = main_queues['risar_error_1']
error_2_queue_name = main_queues['risar_error_2']
remote_queues = app.config['mis_queues']


def get_celery_queues(conf):
    # supervisor = safe_traverse(conf, 'common', 'celery_worker', 'configens', 'supervisor')
    # prefix = safe_traverse(conf, 'deployment', 'prefix')
    res = [
        # Queue('sir_test_celerybeat_queue', exchange=Exchange('sir_test_celerybeat_queue')),
        Queue(main_queue_name, exchange=Exchange(main_queue_name)),
        Queue(error_1_queue_name, exchange=Exchange(error_1_queue_name)),
        Queue(error_2_queue_name, exchange=Exchange(error_2_queue_name)),
    ]
    res.extend([Queue(q_name, exchange=Exchange(q_name)) for q_name in remote_queues.items()])
    return tuple(res)
