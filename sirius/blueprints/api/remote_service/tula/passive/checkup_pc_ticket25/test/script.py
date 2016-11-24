#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import edit_checkup_first_ticket25
from .test_data import test_checkup_first_ticket25_data_error_1, test_checkup_first_ticket25_data_1, \
    test_checkup_first_ticket25_data_2
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestCheckupFirstTicket25:

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
        remote_checkup_first_ticket25_id = 324
        # test_checkup_first_ticket25_data_2['card_id'] = remote_card_id
        # test_checkup_first_ticket25_data_error_1['result_action_id'] = remote_checkup_first_ticket25_id
        result = edit_checkup_first_ticket25(testapp, session, remote_card_id,
                                             remote_checkup_first_ticket25_id, test_checkup_first_ticket25_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def test_edit(self, testapp):
        remote_card_id = 324
        remote_checkup_first_ticket25_id = 324
        # test_checkup_first_ticket25_data_2['card_id'] = remote_card_id
        # test_checkup_first_ticket25_data_2['result_action_id'] = remote_checkup_first_ticket25_id
        result = edit_checkup_first_ticket25(testapp, session, remote_card_id,
                                             remote_checkup_first_ticket25_id, test_checkup_first_ticket25_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
