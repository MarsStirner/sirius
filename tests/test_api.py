#! coding:utf-8
"""


@author: BARS Group
@date: 05.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.remote_service.lib.test.connect import make_login, release_token
from sirius.blueprints.api.remote_service.tula.passive.client.test.request import \
    create_client, edit_client, delete_client
from sirius.blueprints.api.remote_service.tula.passive.client.test.test_data import \
    test_client_data_1, test_client_data_2, test_client_data_error_1

session = None
class TestClient:

    def test_auth(self):
        with app.app_context():
            with make_login() as sess:
                global session
                session = sess
                print 'test_auth', sess

    def test_validation_error(self, testapp):
        print 'test_validation', session
        remote_client_id = 324
        result = create_client(testapp, session, remote_client_id, test_client_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def _test_create(self, testapp):
        remote_client_id = 324
        result = create_client(testapp, session, remote_client_id, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        session = (None, None)
        remote_client_id = 324
        result = create_client(testapp, session, remote_client_id, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        session = (None, None)
        remote_client_id = 324
        result = edit_client(testapp, session, remote_client_id, test_client_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        session = (None, None)
        remote_client_id = 324
        result = delete_client(testapp, session, remote_client_id)
        code = result['meta']['code']
        assert code == 200

    def test_logout(self):
        with app.app_context():
            release_token(session[0])
