# coding: utf-8
from sirius.blueprints.api.test.connect import \
    make_api_request, make_test_api_request


def request_remote(testapp, session, data):
    url = u'/risar/api/request/remote/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result


def request_local(testapp, session, data):
    url = u'/risar/api/request/local/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result


def send_event_remote(testapp, session):
    url = u'/risar/api/send/event/remote/'
    result = make_test_api_request(testapp, 'post', url, session)
    # result = make_api_request('post', url, session)
    return result
