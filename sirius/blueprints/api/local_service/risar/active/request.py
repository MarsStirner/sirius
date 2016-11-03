#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.local_service.risar.lib.parser import \
    LocalAnswerParser
from sirius.blueprints.monitor.exception import connect_entry
from .connect import make_api_request, make_login


@connect_entry(login=make_login)
def request_by_url(method, url, data, session=None):
    parser = LocalAnswerParser()
    response = make_api_request(method, url, session, data)
    parser.check(response)
    return parser, response


def request_by_req(req):
    req_meta = req['meta']
    parser, response = request_by_url(req_meta['dst_method'], req_meta['dst_url'], None)
    return parser.get_data(response)


def create(data):
    from sirius.app import app
    url = u'/risar/api/integration/0/card/%s/checkup/obs/first/' % card_id
    with app.app_context():
        with make_login() as session:
            result = make_api_request('post', url, session, data)
    return result
