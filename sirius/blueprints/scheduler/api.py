#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.monitor.exception import InternalError
from sirius.models.system import SystemCode
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from sirius.models.operation import OperationCode
from .models import Schedule


class Scheduler(object):
    def run(self):
        schedules = Schedule.get_schedules_to_execute()
        for schedule in schedules:
            with schedule.acquire_group_lock() as is_success:
                if is_success:
                    for req_data in schedule.schedule_group.get_requests():
                        self.execute(req_data)
                    return

    def execute(self, req_data):
        from sirius.blueprints.api.local_service.producer import LocalProducer

        entity_code = req_data.entity.code
        system_code = req_data.system.code
        sampling_method_name = req_data.sampling_method
        if sampling_method_name:
            sampling_method_func = getattr(self, sampling_method_name, None)
            if callable(sampling_method_func):
                sampling_method_func(system_code, entity_code)
            else:
                raise InternalError(
                    'Sampling method (%s) not found' %
                    sampling_method_name
                )
        else:
            msg = self.create_message(system_code, entity_code)
            producer = LocalProducer()
            producer.send(msg)

    def create_message(self, system_code, entity_code):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        msg = Message(None)
        msg.to_remote_service()
        msg.set_request_type()
        meta = msg.get_header().meta
        meta['local_entity_code'] = entity_code
        meta['local_operation_code'] = OperationCode.READ_MANY
        meta['remote_system_code'] = system_code
        return msg

    def get_measures_results(self, system_code, entity_code):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msgs = producer.send(msg, async=False)
        for card_msg in card_msgs:
            card_data = card_msg.get_data()

            # /api/integration/<int:api_version>/card/<card_id>/measures/list/
            measures_list_method = reformer.get_api_method(
                SystemCode.LOCAL, RisarEntityCode.MEASURE, OperationCode.READ_MANY
            )
            msg = Message(None)
            msg.to_local_service()
            msg.set_request_type()
            msg.set_immediate_answer()
            msg.set_method(
                measures_list_method['method'],
                measures_list_method['template_url'] % card_data['card_id'],
            )
            producer = RemoteProducer()
            measures_msgs = producer.send(msg, async=False)
            for measure_msg in measures_msgs:
                measure_data = measure_msg.get_data()

                msg = self.create_message(system_code, entity_code)  # searchServiceRend
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    RisarEntityCode.CLIENT: card_data['client_id'],
                    RisarEntityCode.CARD: card_data['card_id'],
                    RisarEntityCode.MEASURE: measure_data['measure_id'],
                }
                producer = LocalProducer()
                producer.send(msg)
