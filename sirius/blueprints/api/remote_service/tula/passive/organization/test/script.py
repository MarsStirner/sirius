#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_organization, edit_organization, delete_organization
from .test_data import test_organization_data_error_1, test_organization_data_1, \
    test_organization_data_2
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestOrganization:

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
        remote_organization_id = 324
        result = create_organization(testapp, session, remote_organization_id, test_organization_data_error_1)
        code = result['meta']['code']
        assert code == 400

    def _test_create(self, testapp):
        remote_organization_id = 324
        result = create_organization(testapp, session, remote_organization_id, test_organization_data_1)
        code = result['meta']['code']
        assert code == 200

    def _test_resend(self, testapp):
        remote_organization_id = 324
        result = create_organization(testapp, session, remote_organization_id, test_organization_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        remote_organization_id = 324
        result = edit_organization(testapp, session, remote_organization_id, test_organization_data_2)
        code = result['meta']['code']
        assert code == 200

    def _test_delete(self, testapp):
        remote_organization_id = 324
        result = delete_organization(testapp, session, remote_organization_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
