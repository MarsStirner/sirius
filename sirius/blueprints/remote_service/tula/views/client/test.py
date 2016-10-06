# coding: utf-8

from ...lib.test import make_login, make_api_request, make_test_api_request
# from test_data import test_client_data_1, test_client_data_2


def create_client(testapp, session, client_id, data):
    url = u'/tula/api/integration/0/client/%s' % client_id
    result = make_test_api_request(testapp, 'post', url, session, data)
    # result = make_api_request('post', url, session, data)
    return result


def edit_client(testapp, session, client_id, data):
    url = u'/tula/api/integration/0/client/%s' % client_id
    result = make_test_api_request(testapp, 'put', url, session, data)
    # result = make_api_request('put', url, session, data)
    return result


def delete_client(testapp, session, client_id):
    url = u'/tula/api/integration/0/client/%s' % client_id
    # result = make_api_request('delete', url, session)
    result = make_test_api_request(testapp, 'delete', url, session)
    return result


# def test_register_edit_client():
#     with make_login() as session:
#         remote_client_id = 324
#         result = create_client(session, remote_client_id, test_client_data_1)
#         client = result['result']
#         print u'new client data: {0}'.format(repr(client).decode("unicode-escape"))
#
#         try:
#             result = create_client(session, remote_client_id, test_client_data_1)
#         except Exception, e:
#             if '409' in e.message:
#                 print e.message
#             else:
#                 raise e
#
#         result = edit_client(session, remote_client_id, test_client_data_2)
#         client = result['result']
#         print u'edited client data: {0}'.format(repr(client).decode("unicode-escape"))
#
#         result = delete_client(session, remote_client_id)
#         client = result['result']
#         print u'edited client data: {0}'.format(repr(client).decode("unicode-escape"))
