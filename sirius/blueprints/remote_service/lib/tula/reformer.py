#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.remote_service.lib.reformer import Reformer, LocalEntity, \
    Operation


class RemoteEntity(Enum):
    CLIENT = 1


class TulaReformer(Reformer):

    def get_local_entities(self, header_meta, data, addition_data):
        remote_entity_code = header_meta['remote_entity_code']
        if remote_entity_code == RemoteEntity.CLIENT:
            res = self.build_local_client(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected remote_entity_code')
        return res

    def build_local_client(self, header_meta, data, addition_data):
        res = {
            'operation_order': {},
            LocalEntity.CLIENT: [{
                'meta': {
                    'src_entity_code': header_meta['src_entity_code'],
                    'src_id': header_meta['src_main_id'],
                    'dst_entity_code': LocalEntity.CLIENT,
                },
            }],
        }
        main_item = res[LocalEntity.CLIENT][0]
        if header_meta['local_operation_code'] != Operation.DELETE:
            self.set_operation_order(res, LocalEntity.CLIENT, 1)
            main_item['body'] = data
        else:
            self.set_operation_order(res, LocalEntity.CLIENT, 2)

        return res
