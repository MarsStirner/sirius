#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import logging

from sirius.blueprints.api.remote_service.tambov.active.connect import \
    RequestModeCode
from sirius.models.operation import OperationCode

logger = logging.getLogger('simple')


class RemoteAnswer(object):

    def process(self, result, req_meta=None, req_data=None):
        # meta['dst_entity_code']
        logger.debug('request: %s\n response: %s' % (str(req_data), ': '.join((str(result), result.text[:600]))))
        if req_meta['dst_request_mode'] == RequestModeCode.JSON_DATA:
            self.check_json(result)
            if req_meta['dst_operation_code'] in (OperationCode.READ_MANY, OperationCode.READ_ONE):
                res = self.get_data(result)
            elif req_meta['dst_operation_code'] in (OperationCode.ADD, OperationCode.CHANGE):
                res = self.get_params(req_meta['dst_entity_code'], result, req_meta['dst_id_url_param_name'])
            else:
                res = True
        elif req_meta['dst_request_mode'] == RequestModeCode.XML_DATA:
            res = self.xml_to_dict(result)
        else:
            res = result.text
        return res

    def xml_to_dict(self, data):
        # todo:
        # return SafeGet(data)
        return data

    def check_json(self, res):
        pass

    def get_data(self, res):
        return res

    def get_params(self, entity_code, res, id_url_param_name):
        return {'main_id': res}
