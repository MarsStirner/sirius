#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.reformer.api import Builder
from sirius.lib.remote_system import RemoteSystemCode
from sirius.models.operation import OperationCode


class ClientTulaBuilder(Builder):
    remote_sys_code = RemoteSystemCode.TULA

    def build_local_client(self, header_meta, data, addition_data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        res = {
            'operation_order': {},
            # 'header_meta': header_meta,
            RisarEntityCode.CLIENT: [{
                'meta': {
                    'src_system_code': header_meta['remote_system_code'],
                    'src_entity_code': header_meta['remote_entity_code'],
                    'src_operation_code': src_operation_code,
                    'src_id': header_meta['remote_main_id'],
                    'src_id_url_param_name': header_meta['remote_main_param_name'],
                    'dst_entity_code': RisarEntityCode.CLIENT,
                },
            }],
        }
        main_item = res[RisarEntityCode.CLIENT][0]
        if src_operation_code != OperationCode.DELETE:
            self.set_operation_order(res, RisarEntityCode.CLIENT, 1)
            main_item['body'] = data
        else:
            self.set_operation_order(res, RisarEntityCode.CLIENT, 2)

        return res
