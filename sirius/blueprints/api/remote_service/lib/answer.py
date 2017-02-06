#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import logging

from sirius.blueprints.api.remote_service.lib.transfer import \
    RequestModeCode
from sirius.models.operation import OperationCode
from sirius.models.protocol import ProtocolCode

logger = logging.getLogger('simple')


class RemoteAnswer(object):

    def process(self, result, req_meta=None, req_data=None):
        if not req_meta['dst_request_mode']:
            if req_meta['dst_protocol_code'] == ProtocolCode.SOAP:
                req_meta['dst_request_mode'] = RequestModeCode.XML_DATA
            if req_meta['dst_protocol_code'] == ProtocolCode.REST:
                req_meta['dst_request_mode'] = RequestModeCode.JSON_DATA
        # meta['dst_entity_code']
        if req_meta['dst_request_mode'] in (RequestModeCode.JSON_DATA, RequestModeCode.MULTIPART_FILE):
            logger.debug('%s url: %s request: %s\n response: %s' % (result.request.method, result.url, str(req_data), ': '.join((str(result), result.text))))
            self.check_json(result)
            if req_meta['dst_operation_code'] in (OperationCode.READ_MANY, OperationCode.READ_ONE):
                res = self.get_data(result)
            elif req_meta['dst_operation_code'] in (OperationCode.ADD, OperationCode.CHANGE):
                res = self.get_params(req_meta['dst_entity_code'], result, req_meta['dst_id_url_param_name'])
            else:
                res = True
        elif req_meta['dst_request_mode'] == RequestModeCode.XML_DATA:
            if req_meta['dst_protocol_code'] == ProtocolCode.SOAP:
                logger.debug('request: %s\n response: %s' % (str(req_data), str(result).decode('utf-8')))
            elif req_meta['dst_protocol_code'] == ProtocolCode.REST:
                logger.debug('request: %s\n response: %s' % (str(req_data), result.text))
            else:
                logger.debug('request: %s\n response: %s' % (str(req_data), ': '.join((str(result), result.text))))
            res = self.xml_to_dict(result)
            if req_meta['dst_operation_code'] in (OperationCode.ADD, OperationCode.CHANGE, OperationCode.DELETE):
                res = self.get_params_ext(req_meta, res)
        else:
            logger.debug('request: %s\n response: %s' % (str(req_data), ': '.join((str(result), result.text))))
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

    def get_params_ext(self, req_meta, result):
        return {'main_id': result}
