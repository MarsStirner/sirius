#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""


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
