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
    method = None
    url = None
    source_data = None

    # todo: по реализации Reformer станет ясно что еще сюда добавить
    # (ID/params, entity_code)


class Message(object):
    header = None
    body = None

    def __init__(self, data):
        self.header = Header()
        self.body = data

    def get_header(self):
        return self.header

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

    def set_source_data(self, data):
        self.header.source_data = data

    def get_source_data(self):
        return self.header.source_data

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
