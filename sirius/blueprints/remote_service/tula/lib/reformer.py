#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.remote_service.lib.reformer import Reformer, Operation
from sirius.lib.remote_system import RemoteSystemCode


class RemoteEntity(Enum):
    CLIENT = 'client'


class TulaReformer(Reformer):
    remote_sys_code = RemoteSystemCode.TULA

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == RemoteEntity.CLIENT:
            res = self.build_local_client(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected remote_entity_code')
        return res

    def get_remote_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}

    def build_local_client(self, header_meta, data, addition_data):
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])
        res = {
            'operation_order': {},
            # 'header_meta': header_meta,
            self.LocalEntity.CLIENT: [{
                'meta': {
                    'src_system_code': header_meta['remote_system_code'],
                    'src_entity_code': header_meta['remote_entity_code'],
                    'src_operation_code': src_operation_code,
                    'src_id': header_meta['remote_main_id'],
                    'src_id_url_param_name': header_meta['remote_main_param_name'],
                    'dst_entity_code': self.LocalEntity.CLIENT,
                },
            }],
        }
        main_item = res[self.LocalEntity.CLIENT][0]
        if src_operation_code != Operation.DELETE:
            self.set_operation_order(res, self.LocalEntity.CLIENT, 1)
            main_item['body'] = data
        else:
            self.set_operation_order(res, self.LocalEntity.CLIENT, 2)

        return res
