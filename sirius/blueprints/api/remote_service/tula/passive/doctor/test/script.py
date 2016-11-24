#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_doctor, edit_doctor, delete_doctor
from .test_data import test_doctor_data_error_1, test_doctor_data_1, \
    test_doctor_data_2
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestDoctor:

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
        remote_doctor_id = 324
        test_doctor_data_error_1['doctor_id'] = remote_doctor_id
        result = create_doctor(testapp, session, test_doctor_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def _test_create(self, testapp):
        remote_doctor_id = 324
        test_doctor_data_1['doctor_id'] = remote_doctor_id
        result = create_doctor(testapp, session, test_doctor_data_1)
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        remote_doctor_id = 324
        test_doctor_data_1['doctor_id'] = remote_doctor_id
        result = create_doctor(testapp, session, test_doctor_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        remote_org_id = 324
        remote_doctor_id = 324
        test_doctor_data_2['organization'] = remote_org_id
        test_doctor_data_2['regional_code'] = remote_doctor_id
        result = edit_doctor(testapp, session, remote_org_id, remote_doctor_id, test_doctor_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        remote_org_id = 324
        remote_doctor_id = 324
        test_doctor_data_2['organization'] = remote_org_id
        test_doctor_data_2['regional_code'] = remote_doctor_id
        result = delete_doctor(testapp, session, remote_org_id, remote_doctor_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
