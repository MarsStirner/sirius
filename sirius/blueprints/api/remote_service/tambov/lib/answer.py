#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer
from sirius.models.protocol import ProtocolCode


class TambovAnswer(RemoteAnswer):

    def process(self, result, req=None):
        # meta['dst_entity_code']
        if req.protocol == ProtocolCode.REST:
            res = result.json()
        else:
            res = self.xml_to_dict(result)
        return res

    def xml_to_dict(self, data):
        # todo:
        return data
