#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_schedule_ticket, edit_schedule_ticket, delete_schedule_ticket
from .test_data import get_schedule_ticket_data_required
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestScheduleTicket:

    def test_auth(self):
        global session
        if session:
            return
        with app.app_context():
            with make_login() as sess:
                session = sess
                print 'test_auth', sess

    def _test_validation_error(self, testapp):
        print 'test_validation', session
        schedule_ticket_id = 324
        result = create_schedule_ticket(testapp, session, get_schedule_ticket_data_required(schedule_ticket_id))
        code = result['meta']['code']
        assert code == 400

    def _test_create(self, testapp):
        schedule_ticket_id = 324
        result = create_schedule_ticket(testapp, session, get_schedule_ticket_data_required(schedule_ticket_id))
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        schedule_ticket_id = 324
        result = create_schedule_ticket(testapp, session, get_schedule_ticket_data_required(schedule_ticket_id))
        code = result['meta']['code']
        assert code == 200

    def _test_edit(self, testapp):
        schedule_ticket_id = 324
        result = edit_schedule_ticket(testapp, session, schedule_ticket_id, get_schedule_ticket_data_required(schedule_ticket_id))
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        schedule_ticket_id = 324
        result = delete_schedule_ticket(testapp, session, schedule_ticket_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
