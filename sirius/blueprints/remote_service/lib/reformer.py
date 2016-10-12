#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from abc import ABCMeta, abstractmethod
from sirius.blueprints.remote_service.models.matching import MatchingId
from sirius.blueprints.remote_service.models.method import ApiMethod
from sirius.lib.apiutils import ApiException

from sirius.lib.message import Message
from sirius.models.operation import OperationCode


class Reformer(object):
    __metaclass__ = ABCMeta

    orig_msg = None
    # direct = None
    transfer = None
    remote_sys_code = 'remote_sys_code'

    def set_transfer(self, transfer):
        self.transfer = transfer

    def reform_msg(self, msg):
        addition_data = msg.get_missing_data()
        header_meta = msg.get_header().meta
        if msg.is_to_local:
            self.check_sys_code(msg)
            entities = self.get_local_entities(header_meta, msg.get_data(), addition_data)
        elif msg.is_to_remote:
            entities = self.get_remote_entities(header_meta, msg.get_data(), addition_data)
        else:
            raise RuntimeError('Undefined direct')
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

    def reform_req(self, msg):
        header_meta = msg.get_header().meta
        request = self.get_remote_request(header_meta)
        return request

    @abstractmethod
    def get_local_entities(self, header_meta, data, addition_data):
        # реализация в регионе
        return {}

    def conformity_local(self, record, answer, answer_data):
        # сопоставление ID в БД при добавлении данных
        # в record пишем полученное ID для дочерних запросов

        rec_meta = record['meta']
        if rec_meta['dst_operation_code'] == OperationCode.ADD:
            answer_res = answer.process(
                rec_meta['dst_entity_code'],
                answer_data,
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

    def conformity_remote(self, local_data, remote_data):
        # сопоставление ID в БД при добавлении данных
        # todo:
        # в record так же пишем полученное ID
        pass

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
                            raise ApiException(400, 'Nothing to delete')
                    else:
                        # todo: контролировать ли это?
                        # если изменяем, но передаем первый раз, то будет добавление
                        meta['dst_operation_code'] = OperationCode.CHANGE if matching_id_data['dst_id'] else OperationCode.ADD

                set_current_id_func = record['meta'].get('set_current_id_func')
                if set_current_id_func:
                    set_current_id_func(record, meta)

                yield record

    def set_service(self, record, is_to_local):
        meta = record['meta']
        if is_to_local:
            method = ApiMethod.get_method(
                meta['src_entity_code'],
                meta['src_operation_code'],
                'local_system',
            )
        else:
            method = ApiMethod.get_method(
                meta['dst_entity_code'],
                meta['dst_operation_code'],
                self.remote_sys_code,
            )
        meta['dst_method'] = method['method']
        meta['dst_url'] = method['template_url'].replace(
            'api_version'.join(('<int:', '>')),
            '0'
        )
        if meta['src_operation_code'] != OperationCode.ADD:
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

    def set_operation_order(self, dict_, entity, order):
        dict_['operation_order'].setdefault(order, []).append(entity)

    def transfer__send_data(self, entities):
        soo = sorted(entities['operation_order'].items(), key=lambda x: x[0])
        for entity_code in soo:
            entity = entities[entity_code]
            for rk, record in entity.iteritems():
                set_parent_id_func = record['meta'].get('set_parent_id_func')
                if set_parent_id_func:
                    set_parent_id_func(record)
                trans_res = self.transfer.execute(record)
                self.conformity_remote(record, trans_res)

    def transfer__send_request(self, request):
        trans_res = self.transfer.execute(request)
        # if request['dst_protocol_code'] == Protocol.REST:
        #     trans_res = self.transfer.execute(request)
        # elif request['dst_protocol_code'] == Protocol.SOAP:
        #     trans_res = self.transfer.execute(request)
        return trans_res

    def send_local_data(self, entities, request_by_url, answer):
        soo = sorted(entities['operation_order'].items(), key=lambda x: x[0])
        for order, entity_codes in soo:
            for entity_code in entity_codes:
                records = entities[entity_code]
                for record in records:
                    rec_meta = record['meta']
                    set_parent_id_func = rec_meta.get('set_parent_id_func')
                    if set_parent_id_func:
                        set_parent_id_func(record)
                    if rec_meta['skip_resend']:
                        continue
                    url = rec_meta['dst_url']
                    method = rec_meta['dst_method']
                    body = record.get('body')
                    answer_data = request_by_url(method, url, body)
                    self.conformity_local(record, answer, answer_data)

    def get_operation_code_by_method(self, method_code):
        if method_code.upper() == 'POST':
            res = OperationCode.ADD
        elif method_code.upper() == 'PUT':
            res = OperationCode.CHANGE
        elif method_code.upper() == 'DELETE':
            res = OperationCode.DELETE
        else:
            raise Exception('Unexpected method')
        return res

    def create_local_msgs(self, data, method):
        if method.upper() == 'POST':
            res = self.create_local_post_msgs({'added': [data]})
        elif method.upper() == 'PUT':
            res = self.create_local_put_msgs({'changed': [data]})
        elif method.upper() == 'DELETE':
            res = self.create_local_del_msgs({'deleted': [data]})
        else:
            raise Exception('Unexpected method')
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

    def get_local_missing_requests(self, msg):
        # todo:
        # дозапросы в локальную систему
        return missing_requests

    def check_sys_code(self, msg):
        if msg.get_header().meta['remote_system_code'] != self.remote_sys_code:
            raise RuntimeError('Does not match remote_system_code')

    def get_remote_request(self, header_meta):
        raise NotImplementedError
