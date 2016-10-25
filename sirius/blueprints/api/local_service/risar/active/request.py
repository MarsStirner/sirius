#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.monitor.exception import connect_entry
from .connect import make_api_request, make_login


@connect_entry
def request_by_url(method, url, data, parser):
    with make_login() as session:
        response = make_api_request(method, url, session, data)
        parser.check(response)
    return response


def create(data):
    from sirius.app import app
    url = u'/risar/api/integration/0/card/%s/checkup/obs/first/' % card_id
    with app.app_context():
        with make_login() as session:
            result = make_api_request('post', url, session, data)
    return result
