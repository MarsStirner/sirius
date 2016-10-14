#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.remote_service.tambov.lib.answer import TambovAnswer
from sirius.blueprints.api.remote_service.tambov.active.connect import MISClient
from sirius.blueprints.api.remote_service.lib.transfer import Transfer


key = 'd6ba79b126957042a471f8b9d880c978'


class TambovTransfer(Transfer):
    clients = {}
    answer = TambovAnswer()

    def execute(self, reformed_data):
        meta = reformed_data['meta']
        method = meta['dst_method']
        wsdl = meta['dst_url']
        client = self.get_client(wsdl)
        req_method = getattr(client, method)
        kw = {}
        if 'dst_id_url_param_name' in meta:
            kw[meta['dst_id_url_param_name']] = meta['dst_id']
        req_result = req_method(**kw)
        res = self.answer.process(req_result)
        return res

    def get_client(self, wsdl):
        if wsdl not in self.clients:
            self.clients[wsdl] = MISClient(wsdl, key)
        return self.clients[wsdl]
