#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer
from sirius.blueprints.api.remote_service.lib.transfer import \
    RequestModeCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode


class TambovAnswer(RemoteAnswer):

    def get_params(self, entity_code, response, param_name):
        # разбирает ответ локальной системы и достает полезные данные
        result = self.get_data(response)
        if entity_code == TambovEntityCode.SRV_PROTOCOL:
            res = {
                'main_id': result[param_name],
                'param_name': param_name,
            }
        else:
            res = {
                'main_id': result[param_name],
                'param_name': param_name,
            }
        return res

    def get_data(self, response):
        try:
            res = response.json()
        except ValueError:
            res = response.text
        return res


# class SafeGet(object):
#     # опасно, т.к. в имени атрибута м/б опечатка
#
#     def __init__(self, obj):
#         self.obj = obj
#
#     def __getattr__(self, item):
#         return self.get_res(item)
#
#     def __getitem__(self, item):
#         return self.get_res(item)
#
#     def __iter__(self):
#         return self.obj.__iter__()
#
#     def get_res(self, item):
#         res = item in self.obj and self.obj[item] or None
#         if type(res) == 'instance':
#             res = self.__class__(res)
#         return res
