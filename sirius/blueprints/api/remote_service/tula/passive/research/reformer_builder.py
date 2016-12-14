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


class ResearchTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])

        # сопоставление параметров родительских сущностей
        params_map = {
            TulaEntityCode.CARD: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.MEASURE_RESEARCH,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='result_action_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = data
            if data['measure_id']:
                local_measure_id = self.reformer.get_local_id_by_remote(
                    RisarEntityCode.MEASURE,
                    TulaEntityCode.MEASURE,
                    data['measure_id'],
                )
                main_item['body']['measure_id'] = local_measure_id

        return entities
