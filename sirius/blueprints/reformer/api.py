#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from abc import ABCMeta, abstractmethod

from sirius.blueprints.monitor.api import IStreamMeta
from sirius.blueprints.monitor.exception import module_entry, InternalError
from sirius.lib.xform import simplify
from sirius.models.protocol import ProtocolCode
from .models.matching import MatchingId
from .models.method import ApiMethod
from sirius.lib.apiutils import ApiException

from sirius.lib.message import Message
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode


class Reformer(IStreamMeta):
    __metaclass__ = ABCMeta

    orig_msg = None
    # direct = None
    transfer = None
    remote_sys_code = None

    def __init__(self):
        from sirius.blueprints.api.local_service.risar.active.request import \
            request_by_req
        self.local_request_by_req = request_by_req

    def set_transfer(self, transfer):
        self.transfer = transfer

    @module_entry
    def reform_msg(self, msg):
        addition_data = None
        header_meta = msg.get_header().meta
        if msg.is_to_local:
            self.check_sys_code(msg)
            entities = self.get_local_entities(header_meta, msg.get_data(), addition_data)
        elif msg.is_to_remote:
            entities = self.get_remote_entities(header_meta, msg.get_data(), addition_data)
        else:
            raise InternalError('Undefined direct')
        for record in self.set_operation(entities, msg.is_to_local):
            self.set_service(record, msg.is_to_local)
        # res = []
        # for entity in entities:
        #     rfrm_meta = entity['meta']
        #     reformed_msg = Message(entity['body'])
        #     reformed_msg.set_header(msg.get_header())
        #     reformed_msg.set_method(rfrm_meta['dst_method'], rfrm_meta['dst_url'])
        #     res.append(reformed_msg)
        return entities

    @module_entry
    def reform_req(self, msg):
        header_meta = msg.get_header().meta
        request = self.get_remote_request(header_meta)
        return request

    @abstractmethod
    def get_local_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}

    @module_entry
    def conformity_local(self, record, parser, answer):
        # сопоставление ID в БД при добавлении данных
        # в record пишем полученное ID для дочерних запросов
        # здесь должен быть стабильный код, т.к. в локальной системе уже добавились данные

        rec_meta = record['meta']
        if rec_meta['dst_operation_code'] == OperationCode.ADD:
            answer_res = parser.get_params(
                rec_meta['dst_entity_code'],
                answer,
            )
            rec_meta['dst_id'] = answer_res['main_id']
            rec_meta['dst_id_url_param_name'] = answer_res['param_name']
            MatchingId.add(
                local_entity_code=rec_meta['dst_entity_code'],
                local_id=rec_meta['dst_id'],
                local_param_name=rec_meta['dst_id_url_param_name'],
                remote_sys_code=self.remote_sys_code,
                remote_entity_code=rec_meta['src_entity_code'],
                remote_id=rec_meta['src_id'],
                remote_param_name=rec_meta['src_id_url_param_name'],
            )
        elif rec_meta['dst_operation_code'] == OperationCode.DELETE:
            MatchingId.remove(
                remote_sys_code=self.remote_sys_code,
                remote_entity_code=rec_meta['src_entity_code'],
                remote_id=rec_meta['src_id'],
                local_entity_code=rec_meta['dst_entity_code'],
                local_id=rec_meta['dst_id'],
            )

    def conformity_remote(self, record, trans_res):
        # сопоставление ID в БД при добавлении данных
        # в record пишем полученное ID для дочерних запросов
        # здесь должен быть стабильный код, т.к. в удаленной системе уже добавились данные

        rec_meta = record['meta']
        if rec_meta['dst_operation_code'] == OperationCode.ADD:
            rec_meta['dst_id'] = trans_res
            # rec_meta['dst_id_url_param_name'] = answer_res['param_name']
            MatchingId.add(
                local_entity_code=rec_meta['src_entity_code'],
                local_id=rec_meta['src_id'],
                local_param_name=rec_meta['src_id_url_param_name'],
                remote_sys_code=self.remote_sys_code,
                remote_entity_code=rec_meta['dst_entity_code'],
                remote_id=rec_meta['dst_id'],
                remote_param_name=rec_meta['dst_id_url_param_name'],
            )
        elif rec_meta['dst_operation_code'] == OperationCode.DELETE:
            MatchingId.remove(
                remote_sys_code=self.remote_sys_code,
                remote_entity_code=rec_meta['dst_entity_code'],
                remote_id=rec_meta['dst_id'],
                local_entity_code=rec_meta['src_entity_code'],
                local_id=rec_meta['src_id'],
            )

    @abstractmethod
    def get_remote_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}

    def get_missing_requests(self, msg):
        # дозапросы в удаленную систему
        # формируются сообщения в локальную систему для запроса
        # дополнительных данных
        req_msg = Message(None)
        req_msg.to_local_service()
        req_msg.set_request_type()
        req_msg.set_method(method, url)
        req_msg.set_immediate_answer()
        return []

    def set_operation(self, entities, is_to_local):
        """
        Вход
        src_operation_code
        src_entity_code
        src_id
        dst_entity_code

        Выход
        skip_resend
        dst_operation_code
        dst_id_url_param_name
        dst_id

        Вызывает
        set_current_id_func(record)
        """
        for pk, records in entities.iteritems():
            if pk == 'operation_order':
                continue
            for record in records:
                meta = record['meta']
                if is_to_local:
                    matching_id_data = MatchingId.first_local_id(
                        meta['src_entity_code'],
                        meta['src_id'],
                        meta['dst_entity_code'],
                        self.remote_sys_code,
                    )
                else:
                    matching_id_data = MatchingId.first_remote_id(
                        meta['src_entity_code'],
                        meta['src_id'],
                        meta['dst_entity_code'],
                        self.remote_sys_code,
                    )
                meta['skip_resend'] = False
                if meta['src_operation_code'] == OperationCode.ADD:
                    if matching_id_data['dst_id']:
                        # ситуация переотправки сообщений
                        meta['skip_resend'] = True
                    meta['dst_id'] = matching_id_data['dst_id']
                    meta['dst_id_url_param_name'] = matching_id_data['dst_id_url_param_name']
                    meta['dst_operation_code'] = OperationCode.ADD
                else:  # (OperationCode.CHANGE, OperationCode.DELETE)
                    meta['dst_id'] = matching_id_data['dst_id']
                    meta['dst_id_url_param_name'] = matching_id_data['dst_id_url_param_name']
                    if meta['src_operation_code'] == OperationCode.DELETE:
                        meta['dst_operation_code'] = OperationCode.DELETE
                        if not matching_id_data['dst_id']:
                            # если удаляем, но еще не передавали
                            raise ApiException(500, 'Nothing to delete')
                    else:
                        # todo: контролировать ли это?
                        # если изменяем, но передаем первый раз, то будет добавление
                        meta['dst_operation_code'] = OperationCode.CHANGE if matching_id_data['dst_id'] else OperationCode.ADD

                set_current_id_func = record['meta'].get('set_current_id_func')
                if set_current_id_func:
                    set_current_id_func(record)

                yield record

    def set_service(self, record, is_to_local):
        """
        Вход
        dst_entity_code
        dst_operation_code
        dst_id_url_param_name
        dst_id

        Выход
        dst_method
        dst_url
        """
        meta = record['meta']
        method = self.get_api_method(
            SystemCode.LOCAL if is_to_local else self.remote_sys_code,
            meta['dst_entity_code'],
            meta['dst_operation_code'],
        )
        meta['dst_method'] = method['method']
        meta['dst_url'] = method['template_url']
        if meta['dst_operation_code'] != OperationCode.ADD:
            if meta['dst_id_url_param_name']:
                meta['dst_url'] = meta['dst_url'].replace(
                    meta['dst_id_url_param_name'].join(('<int:', '>')),
                    str(meta['dst_id'])
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

    @module_entry
    def send_to_remote_data(self, entities):
        soo = sorted(entities['operation_order'].items(), key=lambda x: x[0])
        for order, entity_codes in soo:
            for entity_code in entity_codes:
                records = entities[entity_code]
                for record in records:
                    set_parent_id_func = record['meta'].get('set_parent_id_func')
                    if set_parent_id_func:
                        set_parent_id_func(record)
                    trans_res = self.transfer.execute(record)
                    self.conformity_remote(record, trans_res)

    @module_entry
    def send_to_local_data(self, entities, request_by_url):
        soo = sorted(entities['operation_order'].items(), key=lambda x: x[0])
        for order, entity_codes in soo:
            for entity_code in entity_codes:
                records = entities[entity_code]
                for record in records:
                    rec_meta = record['meta']
                    set_parent_id_func = rec_meta.get('set_parent_id_func')
                    if set_parent_id_func:
                        set_parent_id_func(record)
                    if rec_meta['skip_resend'] or rec_meta.get('skip_trash'):
                        continue
                    url = rec_meta['dst_url']
                    method = rec_meta['dst_method']
                    body = simplify(record.get('body'))
                    parser, answer = request_by_url(method, url, body)
                    self.conformity_local(record, parser, answer)

    def create_local_msgs(self, data, method):
        if method.upper() == 'POST':
            res = self.create_local_post_msgs({'added': [data]})
        elif method.upper() == 'PUT':
            res = self.create_local_put_msgs({'changed': [data]})
        elif method.upper() == 'DELETE':
            res = self.create_local_del_msgs({'deleted': [data]})
        else:
            raise InternalError('Unexpected method')
        return res

    def create_local_post_msgs(self, diff_data):
        # создание списка сообщений для добавления в локальную систему
        # сущностей, описанных в diff_data
        # todo:
        res = []
        for remote_data in diff_data.get('added'):
            entities = self.reform_msg(remote_data)
            for entity in entities:
                msg = Message(entity['body'])
                msg.set_source_data(entity['meta'])
                msg.to_local_service()
                msg.set_send_data_type()
                res.append(msg)
        return res

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
        msg.set_send_event_type()
        return []

    def from_remote(self, req_msg):
        reform_data = self.get_reformed_data(req_msg)
        miss_req_msgs = self.get_missing_requests(reform_data)

        trans_res = self.transfer.execute(reform_data)
        for msg in trans_res:
            miss_req_msgs = self.get_missing_requests(msg)

    def check_sys_code(self, msg):
        if msg.get_header().meta['remote_system_code'] != self.remote_sys_code:
            raise InternalError('Does not match remote_system_code')

    def get_remote_request(self, header_meta):
        raise NotImplementedError

    def set_remote_request_params(self, req_data):
        """
        Вход в req_meta
        dst_id
        dst_entity_code
        Выход
        dst_id_url_param_name
        ---
        Вход в req_meta
        src_id
        src_entity_code
        dst_entity_code
        Выход
        dst_id
        dst_id_url_param_name
        ---
        Вход в req_meta
        src_parents_params
        Выход
        dst_parents_params
        """
        req_meta = req_data['meta']
        if req_meta['dst_id'] and not req_meta.get('dst_id_url_param_name'):
            matching_id_data = MatchingId.first_remote_param_name(
                req_meta['dst_entity_code'],
                req_meta['dst_id'],
                self.remote_sys_code,
            )
            if matching_id_data['dst_id_url_param_name']:
                req_meta['dst_id_url_param_name'] = matching_id_data['dst_id_url_param_name']
        elif req_meta['src_id'] and not req_meta.get('dst_id'):
            matching_id_data = MatchingId.first_remote_id(
                req_meta['src_entity_code'],
                req_meta['src_id'],
                req_meta['dst_entity_code'],
                self.remote_sys_code,
            )
            if matching_id_data['dst_id']:
                req_meta['dst_id'] = matching_id_data['dst_id']
                req_meta['dst_id_url_param_name'] = matching_id_data['dst_id_url_param_name']
            else:
                raise ApiException(500, 'Entity (%s) has not yet passed' % req_meta['src_entity_code'])
        for src_param_name, params in (req_meta.get('src_parents_params') or {}).items():
            src_entity_code = params['entity']
            src_id = params['id']
            matching_id_data = MatchingId.shortest_first_remote_id(
                src_entity_code,
                src_id,
                self.remote_sys_code,
            )
            if matching_id_data['dst_id']:
                req_meta.setdefault('dst_parents_params', {}).update({
                    matching_id_data['dst_id_url_param_name']: matching_id_data['dst_id']
                })
            else:
                raise ApiException(500, 'Entity (%s) has not yet passed' % src_entity_code)

    def set_request_service(self, req_data, system_code):
        """
        Вход
        dst_operation_code
        dst_entity_code
        dst_id_url_param_name
        dst_id
        Выход
        dst_protocol_code
        dst_method
        dst_url
        -----
        Вход
        src_parents_params
        Выход
        dst_url
        """
        req_meta = req_data['meta']
        method = self.get_api_method(
            system_code,
            req_meta['dst_entity_code'],
            req_meta['dst_operation_code'],
        )
        req_meta.update({
            'dst_protocol_code': method['protocol'],
            'dst_method': method['method'],
            'dst_url': method['template_url'],
        })
        if method['protocol'] == ProtocolCode.REST:
            if req_meta['dst_operation_code'] != OperationCode.READ_MANY:
                req_meta['dst_url'] = req_meta['dst_url'].replace(
                    req_meta['dst_id_url_param_name'].join(('<int:', '>')),
                    str(req_meta['dst_id'])
                )

            for src_param_name, params in (req_meta.get('src_parents_params') or {}).items():
                src_entity_code = params['entity']
                src_id = params['id']
                req_meta['dst_url'] = req_meta['dst_url'].replace(
                    src_param_name.join(('<int:', '>')),
                    str(src_id)
                )

    def create_to_local_messages(self, entity_packages):
        msgs = []
        for entity_code, items in entity_packages['entities'].iteritems():
            for item in items:
                if not item['is_changed']:
                    continue
                msg = Message(item)
                msg.to_local_service()
                msg.set_send_data_type()
                header_meta = msg.get_header().meta
                header_meta.update({
                    'remote_system_code': self.remote_sys_code,
                    'remote_operation_code': item['operation_code'],
                    'remote_entity_code': entity_code,
                    'remote_main_id': item['main_id'],
                    'remote_method': item['method'],
                })
                msgs.append(msg)
        return msgs

    def create_to_remote_messages(self, entity_packages):
        msgs = []
        for entity_code, items in entity_packages['entities'].iteritems():
            for item in items:
                # if not item['is_changed']:
                #     continue
                msg = Message(item)
                msg.to_remote_service()
                msg.set_send_data_type()
                header_meta = msg.get_header().meta
                header_meta.update({
                    'remote_system_code': self.remote_sys_code,
                    'local_system_code': SystemCode.LOCAL,
                    'local_operation_code': item['operation_code'],
                    'local_entity_code': entity_code,
                    'local_main_id': item['main_id'],
                    # 'local_method': item['method'],
                    # todo: test
                    'local_main_param_name': item['main_param_name'],
                    'local_parents_params': item['parents_params'],
                })
                msgs.append(msg)
        return msgs

    @classmethod
    def get_stream_meta(cls, obj):
        if isinstance(obj, Message):
            res = {'header': vars(obj.get_header())}
        elif isinstance(obj, dict):
            res = {'dict len': len(obj)}
        else:
            raise InternalError('Unexpected stream type')
        return res

    def get_local_id_by_remote(self, local_entity_code, remote_entity_code, remote_id):
        res = MatchingId.get_local_id(
            local_entity_code,
            remote_entity_code,
            remote_id,
            self.remote_sys_code,
        )
        return res

    def get_register_entity_match(
        self,
        local_entity_code, local_main_id,
        remote_entity_code, remote_main_id
    ):
        res = MatchingId.add(
            local_entity_code=local_entity_code,
            local_id=local_main_id,
            remote_sys_code=self.remote_sys_code,
            remote_entity_code=remote_entity_code,
            remote_id=remote_main_id,
        )
        return res

    # def get_remote_id_by_local(self, local_entity_code, local_id):
    #     res = MatchingId.get_remote_id(
    #         local_entity_code,
    #         local_id,
    #         self.remote_sys_code,
    #     )
    #     return res

    def get_api_method(self, system_code, entity_code, operation_code):
        res = ApiMethod.get(
            system_code, entity_code, operation_code
        )
        res['template_url'] = res['template_url'].replace(
            'api_version'.join(('<int:', '>')),
            '0'
        )
        return res


class Builder(object):
    remote_sys_code = None

    def __init__(self, reformer):
        self.reformer = reformer
        self.transfer = reformer.transfer
        if self.remote_sys_code != reformer.remote_sys_code:
            raise InternalError('No matched system codes Reformer and Builder')

    def set_operation_order(self, dict_, entity, order):
        dict_['operation_order'].setdefault(order, []).append(entity)

    def get_operation_code_by_method(self, method_code):
        if method_code.upper() == 'POST':
            res = OperationCode.ADD
        elif method_code.upper() == 'PUT':
            res = OperationCode.CHANGE
        elif method_code.upper() == 'DELETE':
            res = OperationCode.DELETE
        else:
            raise InternalError('Unexpected method')
        return res

    def transfer__send_request(self, request):
        trans_res = self.transfer.execute(request)
        return trans_res

    def build_remote_request_common(self, header_meta, dst_entity_code):
        req_data = {
            'meta': {
                'src_entity_code': header_meta['local_entity_code'],
                'src_id': header_meta['local_main_id'],
                'src_parents_params': header_meta['local_parents_params'],
                'dst_system_code': self.remote_sys_code,
                'dst_entity_code': dst_entity_code,
                'dst_operation_code': header_meta['local_operation_code'],
                'dst_id': header_meta['remote_main_id'],
            }
        }
        return req_data

    def get_entity_node(self):
        node = {
            'operation_order': {},
        }
        return node

    def set_main_entity(
        self, node, dst_entity_code, dst_parents_params,
        dst_main_id_name, src_operation_code, src_entity_code,
        src_main_id_name, src_id, level, level_count, set_current_id_func=None
    ):
        def set_current_id_common_func(record):
            entity_meta = record['meta']
            entity_body = record['body']
            entity_body[dst_main_id_name] = entity_meta['dst_id']
            if callable(set_current_id_func):
                set_current_id_func(entity_meta, entity_body)

        item = {
            'meta': {
                # 'src_system_code': SystemCode.LOCAL,
                'src_operation_code': src_operation_code,
                'src_entity_code': src_entity_code,
                'src_id_url_param_name': src_main_id_name,
                'src_id': src_id,
                'dst_entity_code': dst_entity_code,
                'dst_id_url_param_name': dst_main_id_name,
                'dst_parents_params': dst_parents_params,
                'set_current_id_func': set_current_id_common_func,
            },
        }
        node.setdefault(dst_entity_code, []).append(item)
        if src_operation_code != OperationCode.DELETE:
            self.set_operation_order(node, dst_entity_code, level)
        else:
            self.set_operation_order(node, dst_entity_code,
                                     level_count - level + 1)
        return item

    def set_child_entity(
        self, node, main_item, dst_entity_code, dst_parents_params,
        dst_main_id_name, dst_parent_id_name, src_operation_code,
        src_entity_code, src_main_id_name, src_id, level, level_count,
        set_current_id_func=None, set_parent_id_func=None
    ):
        def set_current_id_common_func(record):
            entity_meta = record['meta']
            entity_body = record['body']
            entity_body[dst_main_id_name] = entity_meta['dst_id']
            if callable(set_current_id_func):
                set_current_id_func(entity_meta, entity_body)

        def set_parent_id_common_func(record):
            entity_meta = record['meta']
            parent_meta = entity_meta['parent_entity']['meta']
            entity_body = record['body']
            entity_meta['dst_url'] = entity_meta['dst_url'].replace(
                parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
            )
            entity_body[dst_parent_id_name] = parent_meta['dst_id']
            if callable(set_parent_id_func):
                set_parent_id_func(parent_meta, entity_meta, entity_body)

        item = {
            'meta': {
                'src_operation_code': src_operation_code,
                'src_entity_code': src_entity_code,
                'src_id_url_param_name': src_main_id_name,
                'src_id': src_id,
                'dst_entity_code': dst_entity_code,
                'dst_parents_params': dst_parents_params,
                'dst_id_url_param_name': dst_main_id_name,
                'set_current_id_func': set_current_id_common_func,
                'set_parent_id_func': set_parent_id_common_func,
                'parent_entity': main_item,
            },
        }
        node.setdefault(dst_entity_code, []).append(item)
        if src_operation_code != OperationCode.DELETE:
            self.set_operation_order(node, dst_entity_code, level)
        else:
            self.set_operation_order(node, dst_entity_code,
                                     level_count - level + 1)
        return item

    def reform_parents_params(self, header_meta, src_entity_code, params_map):
        for src_param_name, src_params in (header_meta.get('local_parents_params') or {}).items():
            src_param_entity_code = src_params.get('entity')
            src_param_id = src_params.get('id')
            if src_param_entity_code in params_map:
                dst_entity_code = params_map[src_param_entity_code]['entity']
                dst_param_name = params_map[src_param_entity_code]['param']
                matching_id_data = MatchingId.first_remote_id(
                    src_param_entity_code,
                    src_param_id,
                    dst_entity_code,
                    self.remote_sys_code,
                )
                if matching_id_data['dst_id']:
                    header_meta.setdefault('remote_parents_params', {}).update(
                        {dst_param_name: {'entity': dst_entity_code,
                                          'id': matching_id_data['dst_id']}}
                    )
                else:
                    raise ApiException(500, 'Entity (%s) has not yet passed' % src_entity_code)
            else:
                raise InternalError('Unexpected src_param_entity_code')

    def set_src_parents_entity(self, msg_meta, params_meta):
        # дополнение параметров сущностью, если не указана
        for src_param_name, src_params in (msg_meta.get('src_parents_params') or {}).items():
            src_param_entity_code = src_params.get('entity')
            if not src_param_entity_code:
                if src_param_name in params_meta:
                    src_params['entity'] = params_meta[src_param_name]
                else:
                    raise InternalError('Unexpected src_entity_code')
