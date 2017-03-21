#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import logging

import os
from sirius.blueprints.monitor.exception import InternalError, LoggedException
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from sirius.lib.stream import get_stream_id
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode
from .models import Schedule, SchGrReqExecute

logger = logging.getLogger('simple')


class Scheduler(object):
    def run(self):
        schedules = Schedule.get_schedules_to_execute()
        for schedule in schedules:
            with schedule.acquire_group_lock() as is_success:
                if is_success:
                    for req_data in schedule.schedule_group.get_requests():
                        sch_exec = SchGrReqExecute.begin(req_data)
                        try:
                            self.execute(req_data)
                        except LoggedException:
                            pass
                        finally:
                            sch_exec.end()
                else:
                    logger.info(
                        'Scheduler acquire_group_lock denied for schedule.code=%s' %
                        schedule.code
                    )

    def execute(self, req_data):
        from sirius.blueprints.api.local_service.producer import LocalProducer

        entity_code = req_data.entity.code
        system_code = req_data.system.code
        stream_id = get_stream_id()
        sampling_method_name = req_data.sampling_method
        logger.info('stream_id: %s Scheduler execute %s %s %s' % (stream_id, system_code, entity_code, sampling_method_name))
        if sampling_method_name:
            sampling_method_func = getattr(self, sampling_method_name, None)
            if callable(sampling_method_func):
                sampling_method_func(system_code, entity_code, stream_id)
            else:
                raise InternalError(
                    'Sampling method (%s) not found' %
                    sampling_method_name
                )
        else:
            msg = self.create_message(system_code, entity_code)
            producer = LocalProducer()
            producer.send(msg)

    def create_message(self, system_code, entity_code, operation_code=OperationCode.READ_MANY):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        sub_stream_id = get_stream_id()
        msg = Message(None, sub_stream_id)
        msg.to_remote_service()
        msg.set_request_type()
        meta = msg.get_header().meta
        meta['local_entity_code'] = entity_code
        meta['local_operation_code'] = operation_code
        meta['remote_system_code'] = system_code
        return msg

    ################
    ## Тамбов
    ## todo: убрать методы Тамбова к себе. Возможность построения дозапроса параметров для запроса данных

    def get_measures_results_planned(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        msg = Message(None, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():

            # /api/integration/<int:api_version>/card/<card_id>/measures/list/
            measures_list_method = reformer.get_api_method(
                SystemCode.LOCAL, RisarEntityCode.MEASURE, OperationCode.READ_MANY
            )
            dst_url_params = {}
            dst_url_params.update({
                'card_id': {
                    'entity': RisarEntityCode.CARD,
                    'id': str(card_data['card_id']),
                }
            })
            dst_url_entities = dict((val['entity'], val['id']) for val in dst_url_params.values())
            dst_param_ids = [dst_url_entities[param_entity] for param_entity in measures_list_method['params_entities']]
            dst_url = measures_list_method['template_url'].format(*dst_param_ids)

            msg = Message(None, stream_id)
            msg.to_local_service()
            msg.set_request_type()
            msg.set_immediate_answer()
            msg.set_method(
                measures_list_method['method'],
                dst_url,
            )
            producer = RemoteProducer()
            measures_msg = producer.send(msg, async=False)
            for measure_data in measures_msg.get_data():

                msg = self.create_message(system_code, entity_code)  # searchServiceRend
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                    'measure_id': {'entity': RisarEntityCode.MEASURE, 'id': measure_data['measure_id']},
                }
                producer = LocalProducer()
                producer.send(msg)

    def get_measures_results(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode
        from sirius.blueprints.api.remote_service.tambov.entities import \
            TambovEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        data = None
        # data = {
        #     'filters': {
        #         'id': 14  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        msg = Message(data, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                if not reformer.find_remote_id_by_local(
                    TambovEntityCode.SMART_PATIENT,
                    RisarEntityCode.CARD,
                    card_data['card_id'],
                ):
                    continue

                msg = self.create_message(system_code, entity_code)  # searchServiceRend
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_doctors(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        org_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.ORGANIZATION, OperationCode.READ_MANY
        )
        msg = Message(None, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(org_list_method['method'], org_list_method['template_url'])
        producer = RemoteProducer()
        org_msg = producer.send(msg, async=False)
        for org_data in org_msg.get_data():
            try:
                if not org_data['regionalCode']:
                    continue
                if not org_data['regionalCode'] in ('1434663', '89',):  # todo: для тестов
                    continue
                msg = self.create_message(system_code, entity_code)  # getEmployees
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'regionalCode': {'entity': RisarEntityCode.ORGANIZATION, 'id': org_data['regionalCode']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_times(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        org_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.ORGANIZATION, OperationCode.READ_MANY
        )
        msg = Message(None, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(org_list_method['method'], org_list_method['template_url'])
        producer = RemoteProducer()
        org_msg = producer.send(msg, async=False)
        for org_data in org_msg.get_data():
            try:
                if not org_data['regionalCode']:
                    continue
                if not org_data['regionalCode'] in ('1434663', '89',):  # todo: для тестов
                    continue
                msg = self.create_message(system_code, entity_code)  # getTimes
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'regionalCode': {'entity': RisarEntityCode.ORGANIZATION, 'id': org_data['regionalCode']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_birth_results(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode
        from sirius.blueprints.api.remote_service.tambov.entities import \
            TambovEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        data = None
        # data = {
        #     'filters': {
        #         'id': 14  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(data, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                if not reformer.find_remote_id_by_local(
                    TambovEntityCode.SMART_PATIENT,
                    RisarEntityCode.CARD,
                    card_data['card_id'],
                ):
                    continue

                msg = self.create_message(system_code, entity_code, OperationCode.READ_ONE)  # getBirthResult
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def send_exchange_card(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode
        from sirius.blueprints.api.remote_service.tambov.entities import \
            TambovEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        # todo: фильтр для двойняшек
        data = {
            'filters': {
                'pregnancyWeek': 32,  # в рисар нет таких пока
                # 'id': 22,
            }
        }
        # data = {
        #     'filters': {
        #         'id': 14  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(data, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)

        fname = 'exchange_card_template.xml'
        rel_path = 'sirius/blueprints/api/remote_service/tambov/active/service/'
        with open(os.path.join(rel_path, fname)) as pr:
            template_text = pr.read()
        exch_card_req = {
            'doc': {
                'context_type': 'risar_exchange_card',
                'template_text': template_text,
                'template_name': 'exchange_card',
                'id': 0,
                'context': '',
                'event_id': 345
            }
        }
        for card_data in card_msg.get_data():
            try:
                if not reformer.find_remote_id_by_local(
                    TambovEntityCode.SMART_PATIENT,
                    RisarEntityCode.CARD,
                    card_data['card_id'],
                ):
                    continue

                sub_stream_id = get_stream_id()
                exch_card_req['doc']['event_id'] = card_data['card_id']
                # POST /print_subsystem/fill_template
                exch_card_method = reformer.get_api_method(
                    SystemCode.LOCAL, RisarEntityCode.EXCHANGE_CARD,
                    OperationCode.ADD
                )
                msg = Message(exch_card_req, sub_stream_id)
                msg.to_local_service()
                msg.set_request_type()
                msg.set_immediate_answer()
                msg.set_method(exch_card_method['method'], exch_card_method['template_url'])
                exch_card_msg = producer.send(msg, async=False)

                exch_card_data = {
                    'card_LPU': card_data['card_LPU'],
                    'exch_card': exch_card_msg.get_data(),
                }
                msg = Message(exch_card_data, sub_stream_id)
                msg.to_remote_service()
                msg.set_send_data_type()
                meta = msg.get_header().meta
                meta['local_entity_code'] = entity_code
                meta['local_operation_code'] = OperationCode.ADD
                meta['local_main_param_name'] = 'card_id'
                meta['local_main_id'] = card_data['card_id']
                meta['remote_system_code'] = system_code

                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                    'regionalCode': {'entity': RisarEntityCode.ORGANIZATION, 'id': card_data['card_LPU']},
                }
                LocalProducer().send(msg)
            except LoggedException:
                pass

    def get_hospital_rec(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode
        from sirius.blueprints.api.remote_service.tambov.entities import \
            TambovEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        # /api/integration/<int:api_version>/card/list/
        card_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.CARD, OperationCode.READ_MANY
        )
        # data = {
        #     'filters': {
        #         'id': 3  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(None, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'],
                       card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                if not reformer.find_remote_id_by_local(
                    TambovEntityCode.SMART_PATIENT,
                    RisarEntityCode.CARD,
                    card_data['card_id'],
                ):
                    continue

                msg = self.create_message(system_code, entity_code)  # searchHspRecord
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    ########################################
    ## Тула

    def get_tula_schedules_notused(self, system_code, entity_code, stream_id):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code, stream_id)

        org_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.ORGANIZATION, OperationCode.READ_MANY
        )
        msg = Message(None, stream_id)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(org_list_method['method'],
                       org_list_method['template_url'])
        producer = RemoteProducer()
        org_msg = producer.send(msg, async=False)
        for org_data in org_msg.get_data():

            doctor_list_method = reformer.get_api_method(
                SystemCode.LOCAL, RisarEntityCode.DOCTOR, OperationCode.READ_MANY
            )
            dst_url_params = {}
            dst_url_params.update({
                'organization': {
                    'entity': RisarEntityCode.ORGANIZATION,
                    'id': str(org_data['LPU_id']),
                }
            })
            dst_url_entities = dict(
                (val['entity'], val['id']) for val in dst_url_params.values())
            dst_param_ids = [dst_url_entities[param_entity] for param_entity in
                             doctor_list_method['params_entities']]
            dst_url = doctor_list_method['template_url'].format(*dst_param_ids)

            msg = Message(None, stream_id)
            msg.to_local_service()
            msg.set_request_type()
            msg.set_immediate_answer()
            msg.set_method(
                doctor_list_method['method'],
                dst_url,
            )
            producer = RemoteProducer()
            doctor_msg = producer.send(msg, async=False)
            for doctor_data in doctor_msg.get_data():
                if not doctor_data['regional_code']:
                    # мусор
                    continue
                try:
                    msg = self.create_message(
                        system_code, entity_code, OperationCode.ADD
                    )  # WebSchedule
                    meta = msg.get_header().meta
                    meta['local_parents_params'] = {
                        'LPU_id': {'entity': RisarEntityCode.ORGANIZATION,
                                       'id': org_data['LPU_id']},
                        'regional_code': {'entity': RisarEntityCode.DOCTOR,
                                       'id': doctor_data['regional_code']},
                    }
                    producer = LocalProducer()
                    producer.send(msg)
                except LoggedException:
                    pass
