#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_doctor, edit_doctor, delete_doctor
from .test_data import get_doctor_data_required
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class TestDoctor:

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
        org_id = 1112
        doctor_id = 324
        result = create_doctor(testapp, session, get_doctor_data_required(org_id, doctor_id))
        code = result['meta']['code']
        assert code == 400

    def test_create(self, testapp):
        org_id = 1112
        doctor_id = 324
        result = create_doctor(testapp, session, get_doctor_data_required(org_id, doctor_id))
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        org_id = 1112
        doctor_id = 324
        result = create_doctor(testapp, session, get_doctor_data_required(org_id, doctor_id))
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        org_id = 1112
        doctor_id = 324
        result = edit_doctor(testapp, session, org_id, doctor_id, get_doctor_data_required(org_id, doctor_id))
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        org_id = 1112
        doctor_id = 324
        result = delete_doctor(testapp, session, org_id, doctor_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
