#! coding:utf-8
"""


@author: BARS Group
@date: 05.10.2016

"""
from sirius.blueprints.remote_service.tula.views.client.test import \
    create_client, edit_client, delete_client
from sirius.blueprints.remote_service.tula.views.client.test_data import \
    test_client_data_1, test_client_data_2


class TestClient:

    def test_create(self):
        session = (None, None)
        remote_client_id = 324
        result = create_client(session, remote_client_id, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_resend(self):
        session = (None, None)
        remote_client_id = 324
        result = create_client(session, remote_client_id, test_client_data_1)
        code = result['meta']['code']
        assert code == 200

    def test_edit(self):
        session = (None, None)
        remote_client_id = 324
        result = edit_client(session, remote_client_id, test_client_data_2)
        code = result['meta']['code']
        assert code == 200

    def test_delete(self):
        session = (None, None)
        remote_client_id = 324
        result = delete_client(session, remote_client_id)
        code = result['meta']['code']
        assert code == 200
