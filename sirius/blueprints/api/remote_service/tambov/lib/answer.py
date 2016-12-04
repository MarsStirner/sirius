#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer
from sirius.models.protocol import ProtocolCode


class TambovAnswer(RemoteAnswer):

    def process(self, result, req_meta=None):
        # meta['dst_entity_code']
        if req_meta['dst_protocol_code'] == ProtocolCode.REST:
            res = result.json()
        else:
            res = self.xml_to_dict(result)
        return res

    def xml_to_dict(self, data):
        # todo:
        # return SafeGet(data)
        return data


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
