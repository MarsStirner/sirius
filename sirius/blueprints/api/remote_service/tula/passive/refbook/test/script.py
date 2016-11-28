#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from .request import create_refbook, edit_refbook, delete_refbook
from .test_data import get_refbook_data_required, get_refbook_data_changed
from sirius.blueprints.api.test.connect import make_login, release_token

session = None


class _TestRefbook:

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
        rb_code = 'rbMeasureStatus'
        main_id = 326
        data = get_refbook_data_required(main_id)
        data['code'] = main_id
        result = create_refbook(testapp, session, rb_code, data)
        code = result['meta']['code']
        assert code == 400

    def test_create(self, testapp):
        rb_code = 'rbMeasureStatus'
        main_id = '326'
        result = create_refbook(testapp, session, rb_code, get_refbook_data_required(main_id))
        code = result['meta']['code']
        assert code == 200

    def test_resend(self, testapp):
        rb_code = 'rbMeasureStatus'
        main_id = '326'
        result = create_refbook(testapp, session, rb_code, get_refbook_data_required(main_id))
        code = result['meta']['code']
        assert code == 200

    def test_edit(self, testapp):
        rb_code = 'rbMeasureStatus'
        main_id = '326'
        result = edit_refbook(testapp, session, rb_code, main_id, get_refbook_data_changed(main_id))
        code = result['meta']['code']
        assert code == 200

    def test_delete(self, testapp):
        rb_code = 'rbMeasureStatus'
        main_id = '326'
        result = delete_refbook(testapp, session, rb_code, main_id)
        code = result['meta']['code']
        assert code == 200

    def _test_logout(self):
        with app.app_context():
            release_token(session[0])
