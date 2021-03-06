#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from copy import deepcopy

from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.reformer.api import Builder, RequestEntities
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode


class ScheduleTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        entities = RequestEntities(self.reformer.stream_id)

        if src_operation_code != OperationCode.DELETE:

            def after_send_func(entity_meta, entity_body, answer_body):
                # пишем сопоставления по всем тикетам с записью,
                # чтобы по ним можно было работать в потоке schedule_ticket
                matching_parent = self.reformer.get_by_local_id(
                    remote_entity_code=TulaEntityCode.SCHEDULE,
                    local_entity_code=RisarEntityCode.SCHEDULE,
                    local_id=entity_meta['dst_id'],
                )
                answ_tickets = {}
                extra_answ_tickets = {}
                for answ_st in answer_body.get('schedule_tickets') or ():
                    if answ_st.get('schedule_ticket_id') and answ_st.get('patient'):
                        if answ_st.get('schedule_ticket_type') == '1':
                            extra_answ_tickets.setdefault(
                                answ_st['patient'], []
                            ).append(answ_st['schedule_ticket_id'])
                        else:
                            answ_tickets[(
                                answ_st['time_begin'],
                                answ_st['time_end']
                            )] = answ_st['schedule_ticket_id']
                for req_st in data.get('schedule_tickets') or ():
                    if req_st.get('schedule_ticket_id') and req_st.get('patient'):
                        if req_st.get('schedule_ticket_type') == '1':
                            local_patient_id = self.reformer.find_local_id_by_remote(
                                RisarEntityCode.CLIENT,
                                TulaEntityCode.CLIENT,
                                req_st['patient'],
                            )
                            answ_st_id = extra_answ_tickets[
                                local_patient_id
                            ].pop()
                        else:
                            answ_st_id = answ_tickets[(
                                req_st['time_begin'],
                                req_st['time_end']
                            )]
                        upd_res = self.reformer.update_local_match_parent(
                            TulaEntityCode.SCHEDULE_TICKET,
                            RisarEntityCode.SCHEDULE_TICKET,
                            answ_st_id,
                            matching_parent.id,
                        )
                        if not upd_res:
                            if req_st.get('schedule_ticket_type') == '1':
                                remote_id_prefix = 'outplan'
                                # req_st_id = req_st['schedule_ticket_id'][8:]  # если железно будет префикс
                                req_st_id = req_st['schedule_ticket_id'].lstrip('outplan_')
                            else:
                                remote_id_prefix = 'plan'
                                req_st_id = req_st['schedule_ticket_id']
                            self.reformer.register_entity_match(
                                RisarEntityCode.SCHEDULE_TICKET,
                                answ_st_id,
                                TulaEntityCode.SCHEDULE_TICKET,
                                req_st_id,
                                local_param_name='schedule_ticket_id',
                                remote_param_name='schedule_ticket_id',
                                remote_id_prefix=remote_id_prefix,
                                matching_parent_id=matching_parent.id,
                            )
            main_item = entities.set_main_entity(
                dst_entity_code=RisarEntityCode.SCHEDULE,
                dst_parents_params=header_meta['local_parents_params'],
                dst_main_id_name='schedule_id',
                src_operation_code=src_operation_code,
                src_entity_code=header_meta['remote_entity_code'],
                src_main_id_name=header_meta['remote_main_param_name'],
                after_send_func=after_send_func,
                src_id_prefix=data['time_begin'],
                src_id=header_meta['remote_main_id'],
                level_count=1,
            )
            main_item['body'] = deepcopy(data)
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
