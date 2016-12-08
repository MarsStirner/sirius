#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from sirius.app import app
from sirius.blueprints.monitor.exception import InternalError
from sirius.models.system import SystemCode, RegionCode


class RemoteSystem(object):
    is_init = False

    def initialise(self):
        if not self.is_init:
            # todo:
            pass
        self.is_init = True
        self.region_code = app.config['REGION_CODE']

        remote_queues = app.config['mis_queues']
        # todo:
        self.all_systems = {
            RegionCode.TAMBOV: {
                SystemCode.TAMBOV: remote_queues
            },
            RegionCode.TULA: {
                SystemCode.TULA: remote_queues
            },
        }

    def get_codes(self):
        self.initialise()
        return self.all_systems[self.region_code].keys()

    def get_queue_names(self, system_code):
        self.initialise()
        # todo: упростить
        res = []
        for x in self.all_systems[self.region_code][system_code]:
            res.extend(x.values())
        return res

    def is_active(self, rmt_sys_code):
        self.initialise()
        # todo: определять по сущности (методу)
        return False

    def is_passive(self, rmt_sys_code):
        self.initialise()
        # todo: определять по сущности (методу)
        return True

    def get_event_system_code(self):
        # код пассивной системы, работающей с событиями
        self.initialise()
        # todo:
        return SystemCode.TULA

remote_system = RemoteSystem()
