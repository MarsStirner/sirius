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

        res_param = None
        result = []
        for req in reformed_data:
            url = req.url
            if res_param:
                url = url.replace(req.url_param, res_param)
            req_result = self.api_request(req.method, url, session, req.data)
            data = self.answer.process(req_result)
            res_param = data.get(req.res_param)
            result.append(data)
        return result
