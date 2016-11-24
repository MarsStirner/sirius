#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_childbirth, edit_childbirth, delete_childbirth
from .test_data import test_childbirth_data_error_1, test_childbirth_data_1, \
    test_childbirth_data_2
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestChildbirth:

    def test_auth(self):
        global session
        if session:
            return
        with app.app_context():
            with make_login() as sess:
                session = sess
                print 'test_auth', sess

    def test_validation_error(self, testapp):
        print 'test_validation', session
        remote_card_id = 324
        # remote_childbirth_id = 324
        # test_childbirth_data_2['card_id'] = remote_card_id
        # test_childbirth_data_error_1['result_action_id'] = remote_childbirth_id
        result = create_childbirth(testapp, session, remote_card_id, test_childbirth_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def _test_create(self, testapp):
        remote_card_id = 324
        # remote_childbirth_id = 324
        # test_childbirth_data_2['card_id'] = remote_card_id
        # test_childbirth_data_1['result_action_id'] = remote_childbirth_id
        result = create_childbirth(testapp, session, remote_card_id, test_childbirth_data_1)
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        remote_card_id = 324
        # remote_childbirth_id = 324
        # test_childbirth_data_1['result_action_id'] = remote_childbirth_id
        result = create_childbirth(testapp, session, remote_card_id, test_childbirth_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        remote_card_id = 324
        # remote_childbirth_id = 324
        # test_childbirth_data_2['card_id'] = remote_card_id
        # test_childbirth_data_2['result_action_id'] = remote_childbirth_id
        result = edit_childbirth(testapp, session, remote_card_id, test_childbirth_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        remote_card_id = 324
        # remote_childbirth_id = 324
        # test_childbirth_data_2['card_id'] = remote_card_id
        # test_childbirth_data_2['result_action_id'] = remote_childbirth_id
        result = delete_childbirth(testapp, session, remote_card_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
