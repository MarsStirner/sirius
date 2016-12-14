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


class ScheduleTicketTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        msg_meta['src_operation_code'] = self.get_operation_code_by_method(msg_meta['src_method'])
        schedule_ticket_data = msg.get_data()

        # дополнение параметров сущностью, если не указана
        params_meta = {'client_id': RisarEntityCode.CLIENT}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_entity = msg_meta['src_entity_code']

        item = package.add_main_pack_entity(
            entity_code=src_entity,
            operation_code=msg_meta['src_operation_code'],
            method=msg_meta['dst_method'],
            main_param_name='schedule_ticket_id',
            main_id=msg_meta['src_main_id'],
            parents_params=msg_meta['src_parents_params'],
            data=schedule_ticket_data,
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
        schedule_ticket_data = pack_entity['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CLIENT: {
                'entity': TulaEntityCode.CLIENT, 'param': 'client_id'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=TulaEntityCode.SCHEDULE_TICKET,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='schedule_ticket_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = schedule_ticket_data
            main_item['body']['schedule_id'] = self.reformer.get_remote_id_by_local(
                TulaEntityCode.SCHEDULE,
                RisarEntityCode.SCHEDULE,
                main_item['body']['schedule_id'],
            )

        return entities


# main_item['body'] = {
#     'schedule_ticket_id': schedule_ticket_data[''],
#     'hospital': schedule_ticket_data['hospital'],
#     'doctor': schedule_ticket_data['doctor'],
#     'date': schedule_ticket_data['date'],
#     'time': schedule_ticket_data['time'],
# }
