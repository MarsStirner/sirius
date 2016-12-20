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


class DoctorTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])

        # сопоставление параметров родительских сущностей
        params_map = {
            TulaEntityCode.ORGANIZATION: {
                'entity': RisarEntityCode.ORGANIZATION, 'param': 'organization'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.DOCTOR,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='regional_code',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = data.copy()
            if 'department' in data:
                # при ПОСТ сопоставления еще нет и писать филиал некуда
                # сейчас филиал дозапрашивается при записи на прием
                # self.save_doct_filial(data['regional_code'], data['department'])
                del main_item['body']['department']

        return entities

    def save_doct_filial(self, doct_code, filial_code):
        if not filial_code:
            return
        self.reformer.update_remote_match_prefix(
            TulaEntityCode.DOCTOR,
            RisarEntityCode.DOCTOR,
            doct_code,
            filial_code,
        )
