#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
import os
from sirius.app import app
from sirius.blueprints.api.local_service.risar.active.request import \
    request_by_url as risar_request_by_url
from .test_data import request_tambov_patient_1, request_risar_first_checkup_2159, \
    request_tambov_register_patient_card, request_risar_second_checkup_2159, \
    request_risar_measures_139, create_risar_card_1, \
    get_request_risar_get_measure_research, request_risar_first_checkup_31, \
    request_risar_measures_3, request_risar_second_checkup_60, \
    save_request_risar_get_measure_research
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
        result = request_remote(testapp, session, request_tambov_patient_1)
        code = result['meta']['code']
        assert code == 200

    def _test_local_id_by_remote_id(self, testapp):  # запрос id рисар пациента
        result = request_client_local_id_by_remote_id(testapp, session, request_tambov_patient_1)
        code = result['meta']['code']
        assert code == 200

    def _test_first_exam_patient(self, testapp):  # бизнес процесс первичного приема пациента
        # Добавляем/обновляем пациента по UID мис
        result = request_remote(testapp, session, request_tambov_patient_1)
        code = result['meta']['code']
        assert code == 200
        # Запрашиваем ID рисар по UID мис
        result = request_client_local_id_by_remote_id(testapp, session, request_tambov_patient_1)
        code = result['meta']['code']
        assert code == 200
        client_id = result['result']

        # создаем в рисар карту для пациента (в реальности создавать, если нет открытой)
        if 0:
            # data = create_risar_card_1.copy()
            # data['client_id'] = str(client_id)
            # parser, response = risar_request_by_url(
            #     'post',
            #     'http://127.0.0.1:6600/risar/api/integration/0/card/',
            #     data
            # )
            # code = response.status_code
            # assert code == 200
            # card_id = parser.get_data()['card_id']
            card_id = 139

            # записать ID карты в шину, если создавалась новая
            data = request_tambov_register_patient_card.copy()
            data['local_main_id'] = card_id
            result = request_register_card_idents(testapp, session, data)
            code = result['meta']['code']
            assert code == 200

        # переход на страницу карты пациента по ID карты (/risar/inspection.html?event_id=127)

        # сохранение первичного осмотра пациента, запрос выдачи талона
        result = request_local(testapp, session, request_risar_first_checkup_31)
        code = result['meta']['code']
        assert code == 200

        # сохранение мероприятий
        result = request_local(testapp, session, request_risar_measures_3)
        code = result['meta']['code']
        assert code == 200

        # сохранение повторного осмотра пациента, запрос выдачи талона
        result = request_local(testapp, session, request_risar_second_checkup_60)
        code = result['meta']['code']
        assert code == 200

        # сохранение мероприятий
        result = request_local(testapp, session, request_risar_measures_3)
        code = result['meta']['code']
        assert code == 200


    def _test_change_risar_checkup_first(self, testapp):
        # сохранение повторного осмотра пациента, запрос выдачи талона
        result = request_local(testapp, session, request_risar_first_checkup_31)
        code = result['meta']['code']
        assert code == 200

        # сохранение мероприятий
        # result = request_local(testapp, session, request_risar_measures_3)
        # code = result['meta']['code']
        # assert code == 200

    def test_change_risar_checkup_second(self, testapp):
        # сохранение повторного осмотра пациента, запрос выдачи талона
        result = request_local(testapp, session, request_risar_second_checkup_60)
        code = result['meta']['code']
        assert code == 200

        # сохранение мероприятий
        # result = request_local(testapp, session, request_risar_measures_3)
        # code = result['meta']['code']
        # assert code == 200

    def _test_change_risar_measures(self, testapp):
        # сохранение мероприятий
        result = request_local(testapp, session, request_risar_measures_3)
        code = result['meta']['code']
        assert code == 200

    def _test_save_referral(self, testapp):
        # сохранение направления
        result = request_local(testapp, session, save_request_risar_get_measure_research(3, 154))
        code = result['meta']['code']
        assert code == 200

    def _test_change_risar_checkup(self, testapp):
        result = request_local(testapp, session, request_risar_second_checkup_2159)
        code = result['meta']['code']
        assert code == 200

    def _test_create_measure_research(self, testapp):
        result = request_local(testapp, session, get_request_risar_get_measure_research(139, 5637))
        code = result['meta']['code']
        assert code == 200

    def _test_import_diags(self):
        from sirius.blueprints.api.remote_service.tambov.lib.transfer import \
            TambovTransfer
        from sirius.blueprints.reformer.api import DataRequest
        from sirius.models.protocol import ProtocolCode
        with open('diagsf.csv', 'w') as diagsf:
            transfer = TambovTransfer()
            for partNumber in range(1, 31):
                req = DataRequest()
                req.set_req_params(
                    url='https://test68.r-mis.ru/refbooks-ws/refbooksWS?wsdl',
                    method='getRefbookPartial',
                    protocol=ProtocolCode.SOAP,
                    data={
                        'refbookCode': '1.2.643.5.1.13.3.7728241212886.1.1.13',
                        'version': 'CURRENT',
                        'partNumber': partNumber,
                    },
                )
                rows = transfer.execute(req)
                for row in rows:
                    d_id = d_code = gr_parent = gr_parent_id = None
                    for col in row.column:
                        if col.name == 'ID':
                            d_id = col.data
                        elif col.name == 'CODE':
                            d_code = col.data
                        elif col.name == 'GRANDPARENT_ID':
                            gr_parent = True
                            gr_parent_id = col.data
                        if d_id and d_code and gr_parent:
                            break
                    if not gr_parent_id:
                        continue
                    if d_id and d_code:
                        line = '#'.join((
                            str(d_id),
                            str(d_code),
                        ))
                        diagsf.write(line + '\n')

    def _test_send_exch_card(self):
        from sirius.blueprints.api.remote_service.tambov.lib.transfer import \
            TambovTransfer
        from sirius.models.protocol import ProtocolCode
        fname = 'exchange_card_example.xml'
        rel_path = 'sirius/blueprints/api/remote_service/tambov/active/service/'
        with open(os.path.join(rel_path, fname)) as pr:
            template_text = pr.read()

        transfer = TambovTransfer()
        client = transfer.get_rest_client()
        session = None, None
        req_result = client.make_api_request(
            'post', 'https://test68.r-mis.ru/medservices-ws/service-rs/renderedServiceProtocols/16424035',
            ProtocolCode.SOAP, session, template_text)
        print req_result
