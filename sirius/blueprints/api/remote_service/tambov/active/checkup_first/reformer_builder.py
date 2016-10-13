#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder
from sirius.lib.remote_system import RemoteSystemCode
from sirius.models.operation import OperationCode


class CheckupTambovBuilder(Builder):
    remote_sys_code = RemoteSystemCode.TAMBOV

    ##################################################################
    ##  reform entities checkup

    def build_remote_checkup(self, header_meta, data, addition_data):
        # todo:
        src_entity_code = db_get_local_entity_code(header_meta['local_service_code'])
        src_operation_code = self.get_operation_code_by_method(header_meta['local_method'])
        res = {
            'operation_order': {},
            TambovEntityCode.CHECKUP: [{
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': header_meta['local_main_id'],
                    'dst_entity_code': TambovEntityCode.CHECKUP,
                },
            }],
        }
        main_item = res[TambovEntityCode.CHECKUP][0]
        if src_operation_code != OperationCode.DELETE:
            self.set_operation_order(res, TambovEntityCode.CHECKUP, 1)
            main_item['body'] = {
                'code_1': data['code_1'],
                'code_2': addition_data['src_service_code']['code_2'],
            }
        else:
            self.set_operation_order(res, TambovEntityCode.CHECKUP, 2)

        def set_parent_id(record):
            reform_meta = record['meta']
            parent_meta = reform_meta['parent_entity']['meta']
            reform_meta['dst_url'] = reform_meta['dst_url'].replace(
                parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
            )
            record['body'] = {
                'parent_id': parent_meta['meta']['dst_id'],
            }
        for record in data['fetuses']:
            item = {
                'meta': {
                    'src_entity_code': src_entity_code,
                    'src_id': record['fetus_id'],
                    'dst_entity_code': TambovEntityCode.CHECKUP_FETUS,
                    'set_parent_id_func': set_parent_id,
                    'parent_entity': main_item,
                },
            }
            res.setdefault(TambovEntityCode.CHECKUP_FETUS, []).append(item)
            if src_operation_code != OperationCode.DELETE:
                self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 2)
                item['body'] = {
                    'code_1': record['code_1'],
                    'code_2': addition_data['src_service_code']['code_2'],
                }
            else:
                self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 1)
        return res
