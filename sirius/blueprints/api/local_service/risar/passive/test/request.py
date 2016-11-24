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


def send_event_remote(testapp, session, data):
    url = u'/risar/api/send/event/remote/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result


def request_client_local_id_by_remote_id(testapp, session, data):
    url = u'/risar/api/client/local_id/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('get', url, session, data)
    return result


def request_register_card_idents(testapp, session, data):
    url = u'/risar/api/card/register/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result
