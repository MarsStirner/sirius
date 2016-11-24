#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_client, edit_client, delete_client
from .test_data import test_client_data_error_1, test_client_data_1, \
    test_client_data_2
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestClient:

    def test_mr_auth(self):
        global session
        if session:
            return
        with app.app_context():
            with make_login() as sess:
                session = sess
                print 'test_auth', sess

    def test_validation_error(self, testapp):
        print 'test_validation', session
        remote_client_id = '324'
        test_client_data_error_1['client_id'] = remote_client_id
        result = create_client(testapp, session, test_client_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def test_create(self, testapp):
        remote_client_id = '324'
        test_client_data_1['client_id'] = remote_client_id
        result = create_client(testapp, session, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        remote_client_id = '324'
        test_client_data_1['client_id'] = remote_client_id
        result = create_client(testapp, session, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        remote_client_id = '324'
        test_client_data_2['client_id'] = remote_client_id
        result = edit_client(testapp, session, remote_client_id, test_client_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        remote_client_id = '324'
        result = delete_client(testapp, session, remote_client_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
