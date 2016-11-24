#! coding:utf-8
"""


@author: BARS Group
@date: 22.09.2016

"""
from hitsl_utils.safe import safe_traverse
from kombu import Queue, Exchange
from sirius.models.system import RegionCode
from sirius.app import app

main_queue_name = 'sir_test_risar_main_queue'
error_1_queue_name = 'sir_test_risar_error_1_queue'
error_2_queue_name = 'sir_test_risar_error_2_queue'
mis_tula_queue_name = 'sir_test_mis_tula_queue'
mis_tambov_queue_name = 'sir_test_mis_tambov_queue'

# на каждую МИС региона своя очередь
remote_queues = {
    RegionCode.TULA: [
        mis_tula_queue_name,
    ],
    RegionCode.TAMBOV: [
        mis_tambov_queue_name,
    ],
}

region_code = app.config.get('REGION_CODE')
remote_queue_name_list = remote_queues[region_code]


def get_celery_queues(conf):
    # supervisor = safe_traverse(conf, 'common', 'celery_worker', 'configens', 'supervisor')
    # prefix = safe_traverse(conf, 'deployment', 'prefix')
    res = [
        # Queue('sir_test_celerybeat_queue', exchange=Exchange('sir_test_celerybeat_queue')),
        Queue(main_queue_name, exchange=Exchange(main_queue_name)),
        Queue(error_1_queue_name, exchange=Exchange(error_1_queue_name)),
        Queue(error_2_queue_name, exchange=Exchange(error_2_queue_name)),
    ]
    res.extend([Queue(q_name, exchange=Exchange(q_name)) for q_name in remote_queue_name_list])
    return tuple(res)
