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
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode
from .models import Schedule

logger = logging.getLogger('simple')


class Scheduler(object):
    def run(self):
        schedules = Schedule.get_schedules_to_execute()
        for schedule in schedules:
            logger.debug('Scheduler %s' % schedule.code)
            with schedule.acquire_group_lock() as is_success:
                logger.debug('Scheduler locked %s %s' % (schedule.code, is_success))
                if is_success:
                    for req_data in schedule.schedule_group.get_requests():
                        self.execute(req_data)
                    return  # на след. цикле ошибка DetachedInstanceError:
                    # Parent instance <Schedule> is not bound to a Session;
                    # lazy load operation of attribute 'schedule_group' cannot proceed

    def execute(self, req_data):
        from sirius.blueprints.api.local_service.producer import LocalProducer

        entity_code = req_data.entity.code
        system_code = req_data.system.code
        sampling_method_name = req_data.sampling_method
        logger.info('Scheduler execute %s %s %s' % (system_code, entity_code, sampling_method_name))
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

    def create_message(self, system_code, entity_code, operation_code=OperationCode.READ_MANY):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        msg = Message(None)
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

    def get_measures_results_planned(self, system_code, entity_code):
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

            msg = Message(None)
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
        # data = {
        #     'filters': {
        #         'id': 3  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                msg = self.create_message(system_code, entity_code)  # searchServiceRend
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_doctors(self, system_code, entity_code):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code)

        org_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.ORGANIZATION, OperationCode.READ_MANY
        )
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(org_list_method['method'], org_list_method['template_url'])
        producer = RemoteProducer()
        org_msg = producer.send(msg, async=False)
        for org_data in org_msg.get_data():
            try:
                if not org_data['TFOMSCode']:
                    continue
                # if not org_data['TFOMSCode'] == '1434663':  # права выданы только на это лпу
                #     continue
                msg = self.create_message(system_code, entity_code)  # getLocations
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'TFOMSCode': {'entity': RisarEntityCode.ORGANIZATION, 'id': org_data['TFOMSCode']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_times(self, system_code, entity_code):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        from sirius.blueprints.api.remote_service.producer import RemoteProducer
        from sirius.blueprints.api.local_service.risar.entities import \
            RisarEntityCode

        implement = Implementation()
        reformer = implement.get_reformer(system_code)

        doc_list_method = reformer.get_api_method(
            SystemCode.LOCAL, RisarEntityCode.DOCTOR, OperationCode.READ_MANY
        )
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(doc_list_method['method'], doc_list_method['template_url'])
        producer = RemoteProducer()
        doc_msg = producer.send(msg, async=False)
        for doc_data in doc_msg.get_data():
            try:
                msg = self.create_message(system_code, entity_code)  # getTimes
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'regional_code': {'entity': RisarEntityCode.DOCTOR, 'id': doc_data['regional_code']},
                    'organization': {'entity': RisarEntityCode.ORGANIZATION, 'id': doc_data['organization']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def get_birth_results(self, system_code, entity_code):
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
        # data = {
        #     'filters': {
        #         'id': 3  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'], card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                msg = self.create_message(system_code, entity_code, OperationCode.READ_ONE)  # getBirthResult
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass

    def send_exchange_card(self, system_code, entity_code):
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
        # todo: фильтр для двойняшек
        data = {
            'filters': {
                'pregnancyWeek': 32,  # в рисар нет таких пока
                # 'id': 3,
            }
        }
        msg = Message(data)
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
                'id': '0',  # 1181
                'context_type': 'risar',
                'template_text': template_text,
                'template_name': 'exchange_card',
                'context': {
                    # 'event_id': None,
                    'currentOrgStructure': None,
                    'currentOrganisation': None,
                    'currentPerson': None,  # 2
                }
            }
        }
        for card_data in card_msg.get_data():
            try:
                exch_card_req['doc']['context']['event_id'] = card_data['card_id']
                # /print_subsystem/fill_template
                exch_card_method = reformer.get_api_method(
                    SystemCode.LOCAL, RisarEntityCode.EXCHANGE_CARD,
                    OperationCode.READ_ONE
                )
                msg = Message(exch_card_req)
                msg.to_local_service()
                msg.set_request_type()
                msg.set_immediate_answer()
                msg.set_method(exch_card_method['method'], exch_card_method['template_url'])
                exch_card_msg = producer.send(msg, async=False)

                exch_card_data = {
                    'card_LPU': card_data['card_LPU'],
                    'exch_card': exch_card_msg.get_data(),
                }
                msg = Message(exch_card_data)
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
                    'TFOMSCode': {'entity': RisarEntityCode.ORGANIZATION, 'id': '41'},  # todo: card_data['card_LPU']
                }
                LocalProducer().send(msg)
            except LoggedException:
                pass

    def get_hospital_rec(self, system_code, entity_code):
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
        # data = {
        #     'filters': {
        #         'id': 3  # todo: при тестировании работаем пока с одной картой
        #     }
        # }
        msg = Message(None)
        msg.to_local_service()
        msg.set_request_type()
        msg.set_immediate_answer()
        msg.set_method(card_list_method['method'],
                       card_list_method['template_url'])
        producer = RemoteProducer()
        card_msg = producer.send(msg, async=False)
        for card_data in card_msg.get_data():
            try:
                msg = self.create_message(system_code, entity_code)  # searchHspRecord
                meta = msg.get_header().meta
                meta['local_parents_params'] = {
                    'card_id': {'entity': RisarEntityCode.CARD, 'id': card_data['card_id']},
                }
                producer = LocalProducer()
                producer.send(msg)
            except LoggedException:
                pass
