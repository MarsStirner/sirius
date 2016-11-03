#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.monitor.exception import InternalError
from sirius.celery_queue import mis_tambov_queue_name, mis_tula_queue_name
from sirius.models.system import SystemCode


# class RemoteSystemCode(Enum):
#     TAMBOV = 'tambov'
#     TULA = 'tula'


class RemoteSystem(object):
    is_init = False

    def initialise(self):
        if not self.is_init:
            # todo:
            pass
        self.is_init = True

    def get_code(self, queue_name):
        self.initialise()
        # todo:
        if queue_name == mis_tambov_queue_name:
            res = SystemCode.TAMBOV
        elif queue_name == mis_tula_queue_name:
            res = SystemCode.TULA
        else:
            raise InternalError('Unexpected queue name')
        return res

    # def get_queue_name(self, rmt_sys_code):
    #     self.initialise()
    #     # todo:
    #     return 'qname'

    def is_active(self, rmt_sys_code):
        self.initialise()
        # todo: определять по сущности (методу)
        if rmt_sys_code == SystemCode.TULA:
            return True
        return False

    def is_passive(self, rmt_sys_code):
        self.initialise()
        # todo: определять по сущности (методу)
        if rmt_sys_code != SystemCode.TULA:
            return True
        return False

    def get_event_system_code(self):
        # код пассивной системы, работающей с событиями
        self.initialise()
        # todo:
        return SystemCode.TULA

remote_system = RemoteSystem()
