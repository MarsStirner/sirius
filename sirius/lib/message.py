#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum


class Direct(Enum):
    LOCAL = 1
    REMOTE = 2


class Type(Enum):
    REQUEST = 1
    SEND_DATA = 2
    SEND_EVENT = 3
    RESULT = 4


class Header(object):
    direct = None
    type_ = None

    method = None  # deprecated?
    url = None  # deprecated?
    source_data = None  # deprecated?

    # признак возврата ответа результатом функции (а не отдельным запросом)
    is_immediate_answer = False

    # информация об исходном запросе
    meta = None

    def __init__(self):
        self.meta = {
            'local_entity_code': None,  # не обязательное
            'local_service_code': None,  # можем вычислить сущность
            'local_main_id': None,
            'local_main_param_name': None,
            'local_method': None,
            'local_operation_code': None,  # для запроса планировщиком списка
            'local_parents_params': None,  # для фильтрации запроса по родительским сущностям

            'remote_system_code': None,
            'remote_entity_code': None,
            'remote_service_code': None,  # для справки в логах
            'remote_main_id': None,
            'remote_main_param_name': None,
            'remote_method': None,
            'remote_operation_code': None,  # для передачи из пакета в сущность
        }

        # todo: по реализации Reformer станет ясно что еще сюда добавить
        # todo: скорее всего объединить local и remote (посмотреть на запросах с возвратами)
        # (ID/params, entity_code)


class Message(object):
    header = None
    body = None

    def __init__(self, data):
        self.header = Header()
        self.body = data
        self.missing = None

    def get_header(self):
        return self.header

    def set_header(self, header):
        self.header = header

    def get_data(self):
        return self.body

    def to_local_service(self):
        self.header.direct = Direct.LOCAL

    def to_remote_service(self):
        self.header.direct = Direct.REMOTE

    def set_request_type(self):
        self.header.type_ = Type.REQUEST

    def set_send_data_type(self):
        self.header.type_ = Type.SEND_DATA

    def set_send_event_type(self):
        self.header.type_ = Type.SEND_EVENT

    def set_result_type(self):
        self.header.type_ = Type.RESULT

    def set_method(self, method, url):
        self.header.method = method
        self.header.url = url

    def set_immediate_answer(self):
        self.header.is_immediate_answer = True

    def set_source_data(self, data):
        self.header.source_data = data

    def get_source_data(self):
        return self.header.source_data

    def add_missing_data(self, miss_data):
        self.missing = miss_data

    def get_missing_data(self):
        return self.missing

    @property
    def is_to_local(self):
        return self.header.direct == Direct.LOCAL

    @property
    def is_to_remote(self):
        return self.header.direct == Direct.REMOTE

    @property
    def is_request(self):
        return self.header.type_ == Type.REQUEST

    @property
    def is_send_data(self):
        return self.header.type_ == Type.SEND_DATA

    @property
    def is_send_event(self):
        return self.header.type_ == Type.SEND_EVENT

    @property
    def is_result(self):
        return self.header.type_ == Type.RESULT

    @property
    def is_immediate_answer(self):
        return self.header.is_immediate_answer
