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


class OrgDepartmentTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    def build_local_entities(self, header_meta, data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.ORG_DEPARTMENT,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='regionalCode',
            src_operation_code=src_operation_code,
            src_entity_code=header_meta['remote_entity_code'],
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = data
            # внешний код хранится в рисар в исходном виде
            # if 'organisation_id' in data:
            #     org_id = self.reformer.get_local_id_by_remote(
            #         RisarEntityCode.ORGANIZATION,
            #         TulaEntityCode.ORGANIZATION,
            #         data['organisation_id'],
            #     )
            #     main_item['body']['organisation_id'] = org_id

        return entities
