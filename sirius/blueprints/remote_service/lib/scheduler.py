#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.remote_service.lib.consumer import RemoteConsumer
from sirius.lib.message import Message
from sirius.lib.remote_system import remote_system


class Scheduler(object):
    def execute(self):
        rmt_sys_code = remote_system.get_master_system_code()
        for ent in self.get_entities_list():
            msg = self.create_entity_data_request_msg(ent)
            consumer = RemoteConsumer()
            consumer.process(msg, rmt_sys_code)

    def create_entity_data_request_msg(self, entity):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        # todo:
        msg = Message()
        return msg

    def get_entities_list(self):
        # список кодов сущностей, которые нужно запрашивать как мастер-данные
        # из пассивной системы
        # todo:
        return []
