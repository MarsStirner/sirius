#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.api.remote_service.tambov.lib.answer import TambovAnswer
from sirius.blueprints.api.remote_service.tambov.active.connect import TambovSOAPClient, \
    TambovRESTClient
from sirius.blueprints.api.remote_service.lib.transfer import Transfer
from sirius.blueprints.monitor.exception import connect_entry, module_entry, \
    InternalError
from sirius.blueprints.reformer.api import DataRequest
from sirius.models.protocol import ProtocolCode


class TambovTransfer(Transfer):
    clients = {}
    answer = TambovAnswer()

    @module_entry
    def execute(self, req):
        if isinstance(req, DataRequest):
            req_meta = req.meta
        else:
            req_meta = req['meta']
        if req_meta.get('dst_protocol_code', ProtocolCode.SOAP) == ProtocolCode.SOAP:
            req_result = self.soap_protocol(req)
        elif req_meta['dst_protocol_code'] == ProtocolCode.REST:
            req_result = self.rest_protocol(req)
        else:
            raise InternalError('Unexpected protocol (%s)' % req_meta['dst_protocol_code'])
        res = self.answer.process(req_result, req_meta)
        return res

    def soap_protocol(self, req):
        def common_method(*a, **kw):
            service_method = getattr(client.client.service, req.method)
            return service_method(*a, **kw)
        wsdl_lib_code = 'zeep'
        if TambovEntityCode.BIRTH in req.meta['dst_entity_code']:
            wsdl_lib_code = 'suds'
        client = self.get_soap_client(req.url, wsdl_lib_code)
        req_method = getattr(client, req.method, common_method)
        req_result = connect_entry(function=req_method)(*req.options, **req.data)
        return req_result

    @connect_entry
    def get_soap_client(self, wsdl, wsdl_lib_code):
        if wsdl not in self.clients:
            self.clients[wsdl] = TambovSOAPClient(wsdl, wsdl_lib_code)
        return self.clients[wsdl]

    def rest_protocol(self, req):
        client = self.get_rest_client()
        # req_result = connect_entry(
        #     function=client.make_api_request,
        #     login=client.make_login
        # )(req.method, req.url, req.data)
        session = None, None
        req_result = client.make_api_request(req.method, req.url,
                                             req.protocol, session, req.data)
        return req_result

    def get_rest_client(self):
        rest_client_code = 'rest'
        if rest_client_code not in self.clients:
            self.clients[rest_client_code] = TambovRESTClient()
        return self.clients[rest_client_code]
