# coding: utf-8
from sirius.blueprints.api.test.connect import \
    make_api_request, make_test_api_request


def create_hospitalization(testapp, session, parent_id, data):
    url = u'/tula/api/integration/0/card/%s/measures/hospitalization' % parent_id
    # result = make_test_api_request(testapp, 'post', url, session, data)
    result = make_api_request('post', url, session, data)
    return result


def edit_hospitalization(testapp, session, parent_id, main_id, data):
    url = u'/tula/api/integration/0/card/%s/measures/hospitalization/%s' % (parent_id, main_id)
    # result = make_test_api_request(testapp, 'put', url, session, data)
    result = make_api_request('put', url, session, data)
    return result


def delete_hospitalization(testapp, session, parent_id, main_id):
    url = u'/tula/api/integration/0/card/%s/measures/hospitalization/%s' % (parent_id, main_id)
    result = make_test_api_request(testapp, 'delete', url, session)
    # result = make_api_request('delete', url, session)
    return result
