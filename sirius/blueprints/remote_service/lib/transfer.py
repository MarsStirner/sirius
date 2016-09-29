#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.app import app


class Transfer(object):
    login = None
    api_request = None
    answer = None

    def execute(self, reformed_data):
        with app.app_context():
            with self.login() as session:
                result = self.requests(session, reformed_data)
        return result

    def requests(self, session, reformed_data):
        # todo: вынести работу с запросами в request.py, обеспечив общую сессию

        meta = reformed_data['meta']
        url = meta['remote_url']
        method = meta['remote_method']
        body = meta['body']
        req_result = self.api_request(method, url, session, body)
        res = self.answer.process(req_result)
        return res
