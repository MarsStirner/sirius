#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from copy import deepcopy

from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.reformer.api import Builder, RequestEntities
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode


class ScheduleTicketTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        entities = RequestEntities(self.reformer.stream_id)

        if src_operation_code == OperationCode.DELETE:
            # тела нет, поэтому определяем по ID
            if 'outplan_' in header_meta['remote_main_id']:
                remote_main_id = header_meta['remote_main_id'][8:]
                remote_id_prefix = 'outplan'
            else:
                remote_id_prefix = 'plan'
                remote_main_id = header_meta['remote_main_id']
        else:
            if data['schedule_ticket_type'] == '1':
                remote_id_prefix = 'outplan'
                # remote_main_id = header_meta['remote_main_id'][8:]  # если железно будет префикс
                remote_main_id = header_meta['remote_main_id'].lstrip('outplan_')
            else:
                remote_id_prefix = 'plan'
                remote_main_id = header_meta['remote_main_id']

        def after_send_func(entity_meta, entity_body, answer_body):
            if src_operation_code != OperationCode.DELETE:
                self.reformer.update_local_match_parent(
                    RisarEntityCode.SCHEDULE_TICKET,
                    TulaEntityCode.SCHEDULE_TICKET,
                    answer_body['schedule_ticket_id'],
                    matching_parent_id,
                )
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.SCHEDULE_TICKET,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='schedule_ticket_id',
            src_operation_code=src_operation_code,
            src_entity_code=header_meta['remote_entity_code'],
            src_main_id_name=header_meta['remote_main_param_name'],
            after_send_func=after_send_func,
            src_id_prefix=remote_id_prefix,
            src_id=remote_main_id,
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            # если при инициализации тикет придет раньше своего графика, то упадем здесь
            matching_parent = self.reformer.get_by_remote_id(
                RisarEntityCode.SCHEDULE,
                TulaEntityCode.SCHEDULE,
                data['schedule_id'],
                data['schedule_time_begin'],
            )
            matching_parent_id = matching_parent.id

            main_item['body'] = deepcopy(data)
            main_item['body']['schedule_id'] = matching_parent.local_id
            main_item['body']['schedule_time_begin'] = Undefined
            main_item['body']['schedule_ticket_id'] = ''  # заполняется в set_current_id_common_func
            # внешний код хранится в рисар в исходном виде
            # if 'hospital' in data:
            #     hospital_code = self.reformer.get_local_id_by_remote(
            #         RisarEntityCode.ORGANIZATION,
            #         TulaEntityCode.ORGANIZATION,
            #         data['hospital'],
            #     )
            #     main_item['body']['hospital'] = hospital_code
            # if 'doctor' in data:
            #     doctor_code = self.reformer.get_local_id_by_remote(
            #         RisarEntityCode.DOCTOR,
            #         TulaEntityCode.DOCTOR,
            #         data['doctor'],
            #     )
            #     main_item['body']['doctor'] = doctor_code
            if 'patient' in data:
                patient_code = self.reformer.find_local_id_by_remote(
                    RisarEntityCode.CLIENT,
                    TulaEntityCode.CLIENT,
                    data['patient'],
                )
                # 1 - ИД псевдо пациента "Занято". Бывает нужен,
                # если занято мужчиной, либо пациент еще не приходил
                main_item['body']['patient'] = patient_code or '1'

        return entities
