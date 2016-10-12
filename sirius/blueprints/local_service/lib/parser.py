#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.models.entity import LocalEntityCode


class RequestLocalData(object):
    url = None
    method = None
    # разбирает запрос локальной системы и достает полезные данные

    def __init__(self, data):
        self.validate(data)
        self.get_params(data)

    def validate(self, data):
        # todo:
        pass

    def get_params(self, data):
        self.url = data.get('url')
        self.method = data.get('method')


class LocalAnswer(object):
    def process(self, entity_code, result):
        # разбирает ответ локальной системы и достает полезные данные
        res = None
        data = result['result']
        if entity_code == LocalEntityCode.CLIENT:
            res = {
                'main_id': data['client_id'],
                'param_name': 'client_id',
            }
        return res
