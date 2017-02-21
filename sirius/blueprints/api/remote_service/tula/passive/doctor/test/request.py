# coding: utf-8
from sirius.blueprints.api.test.connect import \
    make_api_request, make_test_api_request


def create_doctor(testapp, session, data):
    url = u'/tula/api/integration/0/doctor/'
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result


def edit_doctor(testapp, session, parent_id, main_id, data):
    url = u'/tula/api/integration/0/doctor/%s/%s' % (parent_id, main_id)
    # result = make_test_api_request(testapp, 'put', url, session, data)
    result = make_api_request('put', url, session, data)
    return result


def delete_doctor(testapp, session, parent_id, main_id):
    url = u'/tula/api/integration/0/doctor/%s/%s' % (parent_id, main_id)
    # result = make_test_api_request(testapp, 'delete', url, session)
    result = make_api_request('delete', url, session)
    return result
