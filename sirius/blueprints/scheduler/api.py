#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from .models import Schedule
from sirius.lib.message import Message
from sirius.models.operation import OperationCode


class Scheduler(object):
    def execute(self):
        from sirius.blueprints.api.remote_service.consumer import RemoteConsumer
        schedules = Schedule.get_schedules_to_execute()
        for schedule in schedules:
            with schedule.acquire_group_lock() as is_success:
                if is_success:
                    for req_data in schedule.schedule_group.get_requests():
                        msg = self.create_message(req_data.entity.code)
                        consumer = RemoteConsumer()
                        consumer.process(msg, req_data.system.code)
                    return

    def create_message(self, entity):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        msg = Message(None)
        msg.to_remote_service()
        msg.set_request_type()
        meta = msg.get_header().meta
        meta['local_entity_code'] = entity
        meta['local_operation_code'] = OperationCode.READ_ALL
        return msg
