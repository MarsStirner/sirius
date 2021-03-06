#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from hitsl_utils.enum import Enum
from sirius.blueprints.monitor.exception import module_entry, connect_entry, \
    InternalError
from sirius.blueprints.reformer.api import DataRequest, ReqEntity
from sirius.models.protocol import ProtocolCode


class Transfer(object):
    clients = {}
    login = None
    api_request = None
    answer = None
    wsdl_lib_code = 'zeep'

    @module_entry
    def execute(self, req):
        if isinstance(req, DataRequest):
            req_meta = req.meta  # .protocol
        else:
            assert isinstance(req, ReqEntity)
            req_meta = req['meta']
        if req_meta.get('dst_protocol_code', ProtocolCode.SOAP) == ProtocolCode.SOAP:
            req_result = self.soap_protocol(req, req_meta)
        elif req_meta['dst_protocol_code'] == ProtocolCode.REST:
            req_result = self.rest_protocol(req, req_meta)
        else:
            raise InternalError('Unexpected protocol (%s)' % req_meta['dst_protocol_code'])
        res = self.answer.process(req_result, req_meta, req.data, req.get_stream_id())
        return res

    def soap_protocol(self, req, req_meta):
        def common_method(*a, **kw):
            service_method = getattr(client.client.service, req.method)
            return service_method(*a, **kw)
        client = self.get_soap_client(req.url)
        req_method = getattr(client, req.method, common_method)
        req_result = connect_entry(function=req_method)(*req.options, **req.data)
        return req_result

    def rest_protocol(self, req, req_meta):
        client = self.get_rest_client()

        @connect_entry
        def request_func(method, url, data, session=None, req_mode=None):
            return client.make_api_request(
                method, url, session,
                data, req_mode=req_mode,
            )
        req_result = request_func(req.method, req.url, req.data, req_mode=req.req_mode)

        # req_result = connect_entry(
        #     function=client.make_api_request,
        #     # login=client.make_login,
        #     # nowait=req_meta['immediate'],
        #     # nowait=req_meta['header'].is_send_event,
        # )(req.method, req.url, req.data, req_mode=req.req_mode)
        # session = None, None
        # req_result = client.make_api_request(
        #     req.method, req.url, session,
        #     req.data, req_mode=req.req_mode,
        # )
        return req_result

    @connect_entry
    def get_soap_client(self, wsdl):
        raise NotImplementedError

    def get_rest_client(self):
        raise NotImplementedError


class RequestModeCode(Enum):
    MULTIPART_FILE = 'multipart_file'
    JSON_DATA = 'json_data'
    XML_DATA = 'xml_data'
