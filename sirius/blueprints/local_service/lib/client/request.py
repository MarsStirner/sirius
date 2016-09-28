#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.app import app
from .connect import make_api_request, make_login


def request_by_url(method, url, data):
    with app.app_context():
        with make_login() as session:
            result = make_api_request(method, url, session, data)
    return result


def create(data):
    url = u'/risar/api/integration/0/card/%s/checkup/obs/first/' % card_id
    with app.app_context():
        with make_login() as session:
            result = make_api_request('post', url, session, data)
    return result
