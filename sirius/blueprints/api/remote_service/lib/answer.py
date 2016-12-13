#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.tambov.active.connect import \
    RequestModeCode


class RemoteAnswer(object):

    def process(self, result, req_meta=None):
        # meta['dst_entity_code']
        if req_meta['dst_request_mode'] == RequestModeCode.JSON_DATA:
            res = result.json()
        elif req_meta['dst_request_mode'] == RequestModeCode.XML_DATA:
            res = self.xml_to_dict(result)
        else:
            res = result
        return res

    def xml_to_dict(self, data):
        # todo:
        # return SafeGet(data)
        return data
