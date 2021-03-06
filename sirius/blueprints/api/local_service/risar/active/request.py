#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import datetime, timedelta

from sirius.blueprints.api.local_service.risar.lib.parser import \
    LocalAnswerParser
from sirius.blueprints.monitor.exception import connect_entry
from .connect import make_api_request, make_login


@connect_entry(login=make_login)
def request_by_url(method, url, data, stream_id, session=None):
    parser = LocalAnswerParser()
    data = data or {}
    # подмешиваем stream_id для отображения в логах
    data['stream_id'] = stream_id
    response = make_api_request(method, url, session, data)
    parser.check(response)
    return parser, response

# login_dt = None
# session = None
# @connect_entry
# def request_by_url(method, url, data):
#     global session, login_dt
#     parser = LocalAnswerParser()
#     if not session or (datetime.today() - login_dt > timedelta(minutes=20)):
#         session = make_login()
#         login_dt = datetime.today()
#     response = make_api_request(method, url, session, data)
#     parser.check(response)
#     return parser, response


def request_by_req(req):
    parser, response = request_by_url(
        req.method, req.url, None, req.get_stream_id()
    )
    return parser.get_data(response)



# def make_appointment(session, data):
#     host = 'http://127.0.0.1:6600'
#     url = u'/risar/api/appointment.json'
#     # result = make_test_api_request(testapp, 'put', url, session, data)
#     result = make_api_request('post', host + url, session, data)
#     return result


# def create_card(session, client_id, ticket_id):
#     url = u'/risar/api/0/gyn/'
#     args = {'client_id': client_id, 'ticket_id': ticket_id}
#     # result = make_test_api_request(testapp, 'put', url, session, data)
#     result = make_api_request('post', url, session, url_args=args)
#     return result


# def create_first_checkup(session, event_id, data):
#     url = u'/risar/api/0/pregnancy/checkup/%s' % event_id
#     # result = make_test_api_request(testapp, 'put', url, session, data)
#     result = make_api_request('post', url, session, data)
#     return result
