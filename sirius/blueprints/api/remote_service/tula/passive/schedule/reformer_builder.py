#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.reformer.api import Builder, RequestEntities
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode


class ScheduleTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        entities = RequestEntities()
        if src_operation_code != OperationCode.DELETE:
            main_item = entities.set_main_entity(
                dst_entity_code=RisarEntityCode.SCHEDULE,
                dst_parents_params=header_meta['local_parents_params'],
                dst_main_id_name='schedule_id',
                src_operation_code=src_operation_code,
                src_entity_code=header_meta['remote_entity_code'],
                src_main_id_name=header_meta['remote_main_param_name'],
                src_id_prefix=data['quota_type'],
                src_id=header_meta['remote_main_id'],
                level_count=1,
            )
            main_item['body'] = data
            main_item['body']['schedule_id'] = ''  # заполняется в set_current_id_common_func
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
            for schedule_ticket in main_item['body'].get('schedule_tickets') or ():
                # if 'schedule_ticket_id' in schedule_ticket:
                #     local_schedule_ticket_id = self.reformer.find_local_id_by_remote(
                #         RisarEntityCode.SCHEDULE_TICKET,
                #         TulaEntityCode.SCHEDULE_TICKET,
                #         schedule_ticket['schedule_ticket_id'],
                #     )
                # PUT отключен, поэтому всегда ''
                schedule_ticket['schedule_ticket_id'] = ''
                if 'patient' in schedule_ticket:
                    patient_code = self.reformer.find_local_id_by_remote(
                        RisarEntityCode.CLIENT,
                        TulaEntityCode.CLIENT,
                        schedule_ticket['patient'],
                    )
                    # 1 - ИД псевдо пациента "Занято". Бывает нужен,
                    # если занято мужчиной, либо пациент еще не приходил
                    schedule_ticket['patient'] = patient_code or '1'
        else:  # delete
            all_matches = self.reformer.find_all_matches_by_remote(
                RisarEntityCode.SCHEDULE,
                TulaEntityCode.SCHEDULE,
                header_meta['remote_main_id'],
            )
            for match in all_matches:
                entities.set_main_entity(
                    dst_entity_code=RisarEntityCode.SCHEDULE,
                    dst_parents_params=header_meta['local_parents_params'],
                    dst_main_id_name='schedule_id',
                    src_operation_code=src_operation_code,
                    src_entity_code=header_meta['remote_entity_code'],
                    src_main_id_name=header_meta['remote_main_param_name'],
                    src_id_prefix=match.remote_id_prefix,
                    src_id=match.remote_id,
                    level_count=1,
                )

        return entities
