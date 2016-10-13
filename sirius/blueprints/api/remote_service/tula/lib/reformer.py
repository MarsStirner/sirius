#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.client.reformer_builder import \
    ClientTulaBuilder
from sirius.blueprints.reformer.api import Reformer
from sirius.lib.remote_system import RemoteSystemCode


class TulaReformer(Reformer):
    remote_sys_code = RemoteSystemCode.TULA

    ##################################################################
    ##  reform entities

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == TulaEntityCode.CLIENT:
            res = ClientTulaBuilder(self.transfer, self.remote_sys_code).build_local_client(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}
