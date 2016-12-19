#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_org_department, edit_org_department, delete_org_department
from .test_data import get_org_department_data_required
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestOrgDepartment:

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
        org_id = 324
        depart_id = 324
        result = create_org_department(testapp, session, get_org_department_data_required(org_id, depart_id))
        code = result['meta']['code']
        assert code == 400

    def test_create(self, testapp):
        org_id = 324
        depart_id = 324
        result = create_org_department(testapp, session, get_org_department_data_required(org_id, depart_id))
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        org_id = 324
        depart_id = 324
        result = create_org_department(testapp, session, get_org_department_data_required(org_id, depart_id))
        code = result['meta']['code']
        assert code == 200

    def _test_edit(self, testapp):
        org_id = 324
        depart_id = 324
        result = edit_org_department(testapp, session, org_id, get_org_department_data_required(org_id, depart_id))
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        depart_id = 324
        result = delete_org_department(testapp, session, depart_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
