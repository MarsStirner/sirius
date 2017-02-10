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
    RequestEntities
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode


class CheckupFirstTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        msg_meta['src_operation_code'] = self.get_operation_code_by_method(msg_meta['src_method'])

        checkup_data = msg.get_data()

        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_entity = msg_meta['src_entity_code']

        item = package.add_main_pack_entity(
            entity_code=src_entity,
            operation_code=msg_meta['src_operation_code'],
            method=msg_meta['dst_method'],
            main_param_name=msg_meta['src_main_param_name'],
            main_id=msg_meta['src_main_id'],
            parents_params=msg_meta['src_parents_params'],
            data=checkup_data,
        )
        return package

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
        checkup_data = pack_entity['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TulaEntityCode.CARD, 'param': 'card_id'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities(self.reformer.stream_id)
        main_item = entities.set_main_entity(
            dst_entity_code=TulaEntityCode.CHECKUP_OBS_FIRST,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='external_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = checkup_data
            main_item['body']['external_id'] = header_meta['local_main_id']

        return entities

