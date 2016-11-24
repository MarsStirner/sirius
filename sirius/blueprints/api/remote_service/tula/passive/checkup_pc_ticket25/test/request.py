# coding: utf-8
from sirius.blueprints.api.test.connect import \
    make_api_request, make_test_api_request


def edit_checkup_first_ticket25(testapp, session, parent_id, main_id, data):
    url = u'/tula/api/integration/0/card/%s/checkup/obs/first/%s/ticket25' % (parent_id, main_id)
    # result = make_test_api_request(testapp, 'put', url, session, data)
    result = make_api_request('put', url, session, data)
    return result
