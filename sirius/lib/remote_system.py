#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""


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
        return 'code'

    # def get_queue_name(self, rmt_sys_code):
    #     self.initialise()
    #     # todo:
    #     return 'qname'

    def is_active(self, rmt_sys_code):
        self.initialise()
        # todo:
        return False

    def is_passive(self, rmt_sys_code):
        self.initialise()
        # todo:
        return False

    def get_master_system_code(self):
        # код пассивной системы с мастер-данными
        self.initialise()
        # todo:
        return 'tambov'

    def get_event_system_code(self):
        # код пассивной системы, работающей с событиями
        self.initialise()
        # todo:
        return 'tambov'

remote_system = RemoteSystem()
