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
from sirius.blueprints.reformer.api import DataRequest, ReqEntity
from sirius.models.protocol import ProtocolCode


class TambovTransfer(Transfer):
    answer = TambovAnswer()

    def soap_protocol(self, req, req_meta):
        self.wsdl_lib_code = 'zeep'
        # # todo: wsdl на этот метод не читается zeep (библиотека на метод)
        # if req_meta.get('dst_entity_code') == TambovEntityCode.BIRTH:
        #     self.wsdl_lib_code = 'suds'
        req_result = super(TambovTransfer, self).soap_protocol(req, req_meta)
        return req_result

    @connect_entry
    def get_soap_client(self, wsdl):
        if wsdl not in self.clients:
            self.clients[wsdl] = TambovSOAPClient(wsdl, self.wsdl_lib_code)
        return self.clients[wsdl]

    def get_rest_client(self):
        rest_client_code = 'rest'
        if rest_client_code not in self.clients:
            self.clients[rest_client_code] = TambovRESTClient()
        return self.clients[rest_client_code]
