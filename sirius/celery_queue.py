#! coding:utf-8
"""


@author: BARS Group
@date: 22.09.2016

"""
from hitsl_utils.safe import safe_traverse
from kombu import Queue, Exchange


main_queue_name = 'bi_risar_main_queue'
error_1_queue_name = 'bi_risar_error_1_queue'
error_2_queue_name = 'bi_risar_error_2_queue'

remote_queue_name_list = [
    'bi_mis_tula_queue',
    'bi_mis_tambov_queue',
]


def get_celery_queues(conf):
    # supervisor = safe_traverse(conf, 'common', 'celery_worker', 'configens', 'supervisor')
    # prefix = safe_traverse(conf, 'deployment', 'prefix')
    res = [
        Queue(main_queue_name, exchange=Exchange(main_queue_name)),
        Queue(error_1_queue_name, exchange=Exchange(error_1_queue_name)),
        Queue(error_2_queue_name, exchange=Exchange(error_2_queue_name)),
    ]
    res.extend([Queue(q_name, exchange=Exchange(q_name)) for q_name in remote_queue_name_list])
    return tuple(res)
