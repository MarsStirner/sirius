#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.lib.message import Message


class RemoteEntity(Enum):
    CHECKUP = 1
    CHECKUP_FETUS = 2


class Operation(Enum):
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'


class Reformer(object):
    orig_msg = None
    # direct = None
    transfer = None

    def set_transfer(self, transfer):
        self.transfer = transfer

    def to_local(self, msg):
        # todo:
        self.orig_msg = msg
        # self.direct = 'local'
        # res = self.reform_msg()
        return res

    def reform_msg(self):
        pass

    def local_conformity(self, remote_data, local_data):
        # сопоставление ID в БД при добавлении данных
        # todo:
        pass

    def remote_conformity(self, local_data, remote_data):
        # сопоставление ID в БД при добавлении данных
        # todo:
        pass

    def to_remote(self, msg, miss_msgs):
        self.remote_sys_code = 'remote_sys_code'
        addition_data = self.get_addition_data(miss_msgs)
        params = msg.get_header().meta
        entities = self.get_entities(params, msg.get_data(), addition_data)
        for record in self.set_operation(params, entities):
            self.set_service(record)
        self.send_entities(entities)

    def get_missing_requests(self, msg):
        # формируются сообщения в локальную систему для запроса
        # дополнительных данных
        req_msg = Message(None)
        req_msg.to_local_service()
        req_msg.set_request_type()
        req_msg.set_method(method, url)
        req_msg.set_immediate_answer()
        return []

    def get_entities(self, params, data, addition_data):
        local_entity_code = db_get_local_entity_code(params['local_service_code'])
        res = {
            'operation_order': {},
            RemoteEntity.CHECKUP: [{
                'meta': {
                    'local_entity_code': local_entity_code,
                    'local_id': params['local_main_id'],
                    'remote_entity_code': RemoteEntity.CHECKUP,
                },
            }],
        }
        main_item = res[RemoteEntity.CHECKUP][0]
        if params['local_operation_code'] != Operation.DELETE:
            self.set_operation_order(res, RemoteEntity.CHECKUP, 1)
            main_item['body'] = {
                'code_1': data['code_1'],
                'code_2': addition_data['local_service_code']['code_2'],
            }
        else:
            self.set_operation_order(res, RemoteEntity.CHECKUP, 2)

        def set_parent_id(record):
            meta = record['meta']
            parent_meta = meta['parent_entity']['meta']
            meta['remote_url'] = meta['remote_url'].replace(
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
            if params['local_operation_code'] != Operation.DELETE:
                self.set_operation_order(res, RemoteEntity.CHECKUP_FETUS, 2)
                item['body'] = {
                    'code_1': record['code_1'],
                    'code_2': addition_data['local_service_code']['code_2'],
                }
            else:
                self.set_operation_order(res, RemoteEntity.CHECKUP_FETUS, 1)
        return res

    def set_operation(self, params, entities):
        for pk, entity in entities.iteritems():
            for rk, record in entity.iteritems():
                meta = record['meta']
                entity_id_data = db_get_entity_id(
                    meta['local_entity_code'],
                    meta['local_id'],
                    meta['remote_entity_code'],
                    self.remote_sys_code,
                )
                if params['local_operation_code'] == Operation.ADD:
                    if entity_id_data['remote_id']:
                        # ситуация переотправки сообщений
                        meta['skip_remote_send'] = True
                    meta['remote_id'] = entity_id_data['remote_id']
                    meta['remote_operation_code'] = Operation.ADD
                else:  # (Operation.CHANGE, Operation.DELETE)
                    meta['remote_id'] = entity_id_data['remote_id']
                    meta['remote_id_url_param_name'] = entity_id_data['remote_id_url_param_name']
                    if params['local_operation_code'] == Operation.DELETE:
                        meta['remote_operation_code'] = Operation.DELETE
                    else:
                        # todo: контролировать ли это?
                        # если изменяем первый уровень, но передаем первый раз, то будет добавление
                        meta['remote_operation_code'] = Operation.CHANGE if entity_id_data['remote_id'] else Operation.ADD
                yield record

    def set_service(self, record):
        meta = record['meta']
        res = db_get_remote_service(
            meta['remote_entity_code'],
            meta['remote_operation_code'],
            self.remote_sys_code,
        )
        meta['remote_method'] = res['method']
        meta['remote_url'] = res['template_url'].replace(
            meta['remote_id_url_param_name'], meta['remote_id']
        )

    def get_addition_data(self, missing_msgs):
        # пока считаем, что конвертировать локальные ID не придется
        res = {}
        for msg in missing_msgs:
            hdr = msg.get_header()
            params = hdr.params
            res[params['local_service_code']] = {
                'params': params,
                'data': msg.get_data(),
            }

    def set_operation_order(self, dict_, entity, order):
        dict_['operation_order'].setdefault(order, []).append(entity)

    def send_entities(self, entities):
        soo = sorted(entities['operation_order'].items(), key=lambda x: x[0])
        for entity_code in soo:
            entity = entities[entity_code]
            for rk, record in entity.iteritems():
                set_parent_id = record['meta'].get('set_parent_id_func')
                if set_parent_id:
                    set_parent_id(record)
                trans_res = self.transfer.execute(record)
                self.remote_conformity(record, trans_res)

    def create_local_msgs(self, data, method):
        if method.upper == 'POST':
            res = self.create_local_post_msgs({'added': data})
        elif method.upper == 'PUT':
            res = self.create_local_put_msgs({'changed': data})
        elif method.upper == 'DELETE':
            res = self.create_local_del_msgs({'deleted': data})
        else:
            raise Exception('Unexpected method')
        return res

    def create_local_post_msgs(self, diff_data):
        # создание списка сообщений для добавления в локальную систему
        # сущностей, описанных в diff_data
        # todo:
        for remote_data in diff_data.get('added'):
            local_data = self.to_local(remote_data)
            msg = Message(local_data)
            msg.set_source_data(remote_data)
        return []

    def create_local_put_msgs(self, diff_data):
        # создание списка сообщений для изменения в локальную систему
        # сущностей, описанных в diff_data
        diff_data.get('changed')
        # todo:
        return []

    def create_local_del_msgs(self, diff_data):
        # создание списка сообщений для удаления в локальную систему
        # сущностей, описанных в diff_data
        diff_data.get('deleted')
        # todo:
        return []

    def get_reformed_data(self, msg):
        return res
