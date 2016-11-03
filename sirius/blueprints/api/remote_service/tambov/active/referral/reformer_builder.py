#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode

encode = WebMisJsonEncoder().default
to_date = lambda x: datetime.strptime(x, '%Y-%m-%d')


class ReferralTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        entities = {}
        entity_packages = {
            'system_code': SystemCode.LOCAL,
            'entities': entities,
        }
        msg_meta = msg.get_relative_meta()
        self.set_measures(msg.get_data(), entities, msg_meta)
        return entity_packages

    def set_measures(self, measures, entities, msg_meta):
        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_operation_code = self.get_operation_code_by_method(msg_meta['src_method'])
        src_entity = msg_meta['src_entity_code']

        for measure_data in measures:
            measure_root_parent = measure_node = {
                'is_changed': False,
                'operation_code': src_operation_code,
                'main_id': measure_data['measure_id'],
                'data': measure_data,

                # 'method': msg_meta['dst_method'],
                'main_param_name': 'measure_id',
                'parents_params': msg_meta['src_parents_params'],
            }
            entities.setdefault(
                src_entity, []
            ).append(measure_node)

    ##################################################################
    ##  reform entities

    def build_remote_entities(self, header_meta, entity_package, addition_data):
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
        measure_data = entity_package['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_parents_params(header_meta, src_entity_code, params_map)

        res = self.get_entity_node()
        main_item = self.set_main_entity(
            node=res,
            dst_entity_code=TambovEntityCode.REFERRAL,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level=1,
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                'id': None,  # проставляется в set_current_id_func
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'referralDate': to_date(measure_data['begin_datetime']),
                'referralOrganizationId': '1434663',
            }

        return res
