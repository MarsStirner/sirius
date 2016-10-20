#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""


class Transfer(object):
    login = None
    api_request = None
    answer = None

    def execute(self, reformed_data):
        # if request['dst_protocol_code'] == Protocol.REST:
        #     trans_res = self.transfer.execute(request)
        # elif request['dst_protocol_code'] == Protocol.SOAP:
        #     trans_res = self.transfer.execute(request)
        from sirius.app import app
        with app.app_context():
            with self.login() as session:
                result = self.requests(session, reformed_data)
        return result

    def requests(self, session, reformed_data):
        # todo: вынести работу с запросами в request.py, обеспечив общую сессию

        meta = reformed_data['meta']
        url = meta['dst_url']
        method = meta['dst_method']
        body = meta['body']
        req_result = self.api_request(method, url, session, body)
        res = self.answer.process(req_result)
        return res
