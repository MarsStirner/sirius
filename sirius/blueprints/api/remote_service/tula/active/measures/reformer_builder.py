#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tula.entities import \
    TulaEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode


class MeasureTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        msg_meta['src_operation_code'] = self.get_operation_code_by_method(msg_meta['src_method'])
        self.set_measures(msg.get_data(), package, msg_meta)
        return package

    def set_measures(self, measures, package, msg_meta):
        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        for measure in measures:
            if not measure['appointment_id']:
                continue
            item = package.add_main_pack_entity(
                entity_code=msg_meta['src_entity_code'],
                operation_code=msg_meta['src_operation_code'],
                method=msg_meta['dst_method'],
                main_param_name=msg_meta['src_main_param_name'],
                main_id=measure['measure_id'],
                parents_params=msg_meta['src_parents_params'],
                data=measure,
            )

            data_req = DataRequest()
            data_req.set_meta(
                dst_system_code=SystemCode.LOCAL,
                dst_entity_code=RisarEntityCode.APPOINTMENT,
                dst_operation_code=OperationCode.READ_ONE,
                dst_id=measure['appointment_id'],
                dst_parents_params=msg_meta['src_parents_params'],
            )
            data_req.req_data['meta']['dst_id_url_param_name'] = 'appointment_id'

            # self.reformer.set_local_id(data_req)
            self.reformer.set_request_service(data_req)
            appointment_data = self.reformer.local_request_by_req(data_req)
            item = package.add_addition_pack_entity(
                root_item=item,
                parent_item=item,
                entity_code=RisarEntityCode.APPOINTMENT,
                main_id=measure['appointment_id'],
                data=appointment_data,
            )

    ##################################################################
    ##  reform entities to remote

    def build_remote_entities(self, header_meta, pack_entity):
        """
        Вход в header_meta
        local_operation_code
        local_entity_code
        local_main_param_name
        local_main_id
        local_parents_params

        Выход в entity
        dst_entity_code
        dst_main_param_name
        """
        measure_data = pack_entity['data']
        appointment_node = pack_entity['addition'][RisarEntityCode.APPOINTMENT][0]
        appoint_data = appointment_node['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TulaEntityCode.CARD, 'param': 'card_id'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=TulaEntityCode.MEASURE,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='measure_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                "measure_id": measure_data.get('measure_id'),
                "measure_type_code": measure_data.get('measure_type_code'),
                "begin_date": measure_data.get('begin_datetime'),
                "end_date": measure_data.get('end_datetime'),
                "status": measure_data.get('status'),
                # ---
                "appointment": {
                    "appointment_id": measure_data.get('appointment_id'),
                    "appointment_code": appoint_data.get('appointment_code'),
                    "appointed_date": appoint_data.get('date'),
                    "appointed_lpu": appoint_data.get('appointed_lpu'),
                    "appointed_doctor": appoint_data.get('appointed_doctor'),
                    "referral_lpu": appoint_data.get('referral_lpu'),
                    "referral_date": appoint_data.get('referral_date'),
                    "execution_time": appoint_data.get('execution_time'),
                    "diagnosis": appoint_data.get('diagnosis'),
                    "indications": measure_data.get('indications'),
                    "parameters": appoint_data.get('parameters'),
                    "comment": appoint_data.get('comment'),
                    "hospitalization_form": appoint_data.get('hospitalization_form'),
                    "operation": appoint_data.get('operation'),
                    "profile": appoint_data.get('profile'),
                    # "bed_profile": appoint_data.get(''),
                },
                "result_action_id": measure_data.get('result_action_id'),
            }

        return entities

