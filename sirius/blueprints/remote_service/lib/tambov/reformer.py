#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.remote_service.lib.reformer import Reformer, LocalEntity, \
    Operation


class RemoteEntity(Enum):
    CHECKUP = 1
    CHECKUP_FETUS = 2


class TambovReformer(Reformer):

    def get_remote_entities(self, header_meta, data, addition_data):
        local_entity_code = header_meta['local_entity_code']
        if local_entity_code == LocalEntity.CHECKUP:
            res = self.build_remote_checkup(header_meta, data, addition_data)
        else:
            raise RuntimeError('Unexpected local_entity_code')
        return res

    def build_remote_checkup(self, header_meta, data, addition_data):
        local_entity_code = db_get_local_entity_code(header_meta['local_service_code'])
        res = {
            'operation_order': {},
            RemoteEntity.CHECKUP: [{
                'meta': {
                    'local_entity_code': local_entity_code,
                    'local_id': header_meta['local_main_id'],
                    'remote_entity_code': RemoteEntity.CHECKUP,
                },
            }],
        }
        main_item = res[RemoteEntity.CHECKUP][0]
        if header_meta['local_operation_code'] != Operation.DELETE:
            self.set_operation_order(res, RemoteEntity.CHECKUP, 1)
            main_item['body'] = {
                'code_1': data['code_1'],
                'code_2': addition_data['local_service_code']['code_2'],
            }
        else:
            self.set_operation_order(res, RemoteEntity.CHECKUP, 2)

        def set_parent_id(record):
            reform_meta = record['meta']
            parent_meta = reform_meta['parent_entity']['meta']
            reform_meta['remote_url'] = reform_meta['remote_url'].replace(
                parent_meta['remote_id_url_param_name'], parent_meta['remote_id']
            )
            record['body'] = {
                'parent_id': parent_meta['meta']['remote_id'],
            }
        for record in data['fetuses']:
            item = {
                'meta': {
                    'local_entity_code': local_entity_code,
                    'local_id': record['fetus_id'],
                    'remote_entity_code': RemoteEntity.CHECKUP_FETUS,
                    'set_parent_id_func': set_parent_id,
                    'parent_entity': main_item,
                },
            }
            res.setdefault(RemoteEntity.CHECKUP_FETUS, []).append(item)
            if header_meta['local_operation_code'] != Operation.DELETE:
                self.set_operation_order(res, RemoteEntity.CHECKUP_FETUS, 2)
                item['body'] = {
                    'code_1': record['code_1'],
                    'code_2': addition_data['local_service_code']['code_2'],
                }
            else:
                self.set_operation_order(res, RemoteEntity.CHECKUP_FETUS, 1)
        return res
