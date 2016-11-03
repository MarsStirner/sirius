#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.client.reformer_builder import \
    ClientTulaBuilder
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Reformer
from sirius.models.system import SystemCode


class TulaReformer(Reformer):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TulaEntityCode.CLIENT:
            res = ClientTulaBuilder(self).build_local_client(header_meta, data, addition_data)
        else:
            raise InternalError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}
