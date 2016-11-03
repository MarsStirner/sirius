#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.local_service.risar.active.request import \
    request_by_url as risar_request_by_url
from .test_data import request_tula_patient_1, request_risar_first_checkup_1995, \
    request_tula_register_patient_card, request_risar_second_checkup_1995, \
    request_risar_measures_127
from .request import request_remote, request_local, \
    request_client_local_id_by_remote_id, request_register_card_idents
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

    def _test_request_by_remote_id(self, testapp):  # запрос пациента из тулы по uid мис
        result = request_remote(testapp, session, request_tula_patient_1)
        code = result['meta']['code']
        assert code == 200

    def _test_local_id_by_remote_id(self, testapp):  # запрос id рисар пациента
        result = request_client_local_id_by_remote_id(testapp, session, request_tula_patient_1)
        code = result['meta']['code']
        assert code == 200

    def test_first_exam_patient(self, testapp):  # бизнес процесс первичного приема пациента
        # Добавляем/обновляем пациента по UID мис
        result = request_remote(testapp, session, request_tula_patient_1)
        code = result['meta']['code']
        assert code == 200
        # Запрашиваем ID рисар по UID мис
        result = request_client_local_id_by_remote_id(testapp, session, request_tula_patient_1)
        code = result['meta']['code']
        assert code == 200
        client_id = result['result']

        # создаем в рисар карту для пациента (в реальности создавать, если нет открытой)
        # data = create_risar_card_1.copy()
        # data['client_id'] = str(client_id)
        # parser, response = risar_request_by_url(
        #     'post',
        #     'http://127.0.0.1:6600/risar/api/integration/0/card/',
        #     data
        # )
        # code = response.status_code
        # assert code == 200
        # card_id = parser.data['card_id']
        # card_id = 127
        #
        # # записать ID карты в шину, если создавалась новая
        # data = request_tula_register_patient_card.copy()
        # data['local_main_id'] = card_id
        # result = request_register_card_idents(testapp, session, data)
        # code = result['meta']['code']
        # assert code == 200

        # переход на страницу карты пациента по ID карты (/risar/inspection.html?event_id=127)

        # сохранение первичного осмотра пациента, запрос выдачи талона
        result = request_local(testapp, session, request_risar_first_checkup_1995)
        code = result['meta']['code']
        assert code == 200

        # сохранение мероприятий
        result = request_local(testapp, session, request_risar_measures_127)
        code = result['meta']['code']
        assert code == 200

    def _test_change_risar_checkup(self, testapp):
        result = request_local(testapp, session, request_risar_second_checkup_1995)
        code = result['meta']['code']
        assert code == 200
