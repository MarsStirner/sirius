#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .test_data import request_tula_patient_1
from .request import request_remote
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class TestLocalApi:

    def test_auth(self):
        global session
        if session:
            return
        with app.app_context():
            with make_login() as sess:
                session = sess
                print 'test_auth', sess

    def test_request_by_remote_id(self, testapp):
        result = request_remote(testapp, session, request_tula_patient_1)
        code = result['meta']['code']
        assert code == 200
