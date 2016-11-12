#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.remote_service.tambov.lib.answer import TambovAnswer
from sirius.blueprints.api.remote_service.tambov.active.connect import MISClient
from sirius.blueprints.api.remote_service.lib.transfer import Transfer
from sirius.blueprints.monitor.exception import connect_entry, module_entry

key = 'd6ba79b126957042a471f8b9d880c978'


class TambovTransfer(Transfer):
    clients = {}
    answer = TambovAnswer()

    @module_entry
    def execute(self, req):
        def common_method(**kw):
            service_method = getattr(client.client.service, req.method)
            return service_method(**kw)

        client = self.get_client(req.url)
        req_method = getattr(client, req.method, common_method)
        req_result = connect_entry(function=req_method)(**req.data)
        res = self.answer.process(req_result)
        return res

    @connect_entry
    def get_client(self, wsdl):
        if wsdl not in self.clients:
            self.clients[wsdl] = MISClient(wsdl, key)
        return self.clients[wsdl]
