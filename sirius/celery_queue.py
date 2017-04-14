#! coding:utf-8
"""


@author: BARS Group
@date: 22.09.2016

"""
from kombu import Queue, Exchange


def get_celery_queues(conf):
    main_queues = conf['main_queues']
    main_queue_name = main_queues['risar_main']
    back_queue_name = main_queues['risar_back']
    error_1_queue_name = main_queues['risar_error_1']
    error_2_queue_name = main_queues['risar_error_2']
    remote_queues = conf['mis_queues']

    res = [
        # Queue('sir_test_celerybeat_queue', exchange=Exchange('sir_test_celerybeat_queue')),
        Queue(main_queue_name, exchange=Exchange(main_queue_name)),
        Queue(back_queue_name, exchange=Exchange(back_queue_name)),
        Queue(error_1_queue_name, exchange=Exchange(error_1_queue_name)),
        Queue(error_2_queue_name, exchange=Exchange(error_2_queue_name)),
    ]
    res.extend([Queue(q_name, exchange=Exchange(q_name)) for q_name in (q.values()[0] for q in remote_queues)])
    return tuple(res)
