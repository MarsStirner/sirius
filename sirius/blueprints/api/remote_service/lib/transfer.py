#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.monitor.exception import module_entry, connect_entry


class Transfer(object):
    login = None
    api_request = None
    answer = None

    @module_entry
    @connect_entry
    def execute(self, req):
        # if request['dst_protocol_code'] == Protocol.REST:
        #     trans_res = self.transfer.execute(request)
        # elif request['dst_protocol_code'] == Protocol.SOAP:
        #     trans_res = self.transfer.execute(request)
        with self.login() as session:
            result = self.requests(session, req)
        return result

    def requests(self, session, req):
        # todo: вынести работу с запросами в request.py, обеспечив общую сессию

        url = req.url
        method = req.method
        body = req['body']
        req_result = self.api_request(method, url, session, body)
        res = self.answer.process(req_result)
        return res
