#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.app import app
from sirius.blueprints.api.local_service.risar.active.test.test_data import \
    get_mr_appointment_data
from sirius.blueprints.api.local_service.risar.passive.test.request import \
    send_event_remote, request_local
from sirius.blueprints.api.local_service.risar.passive.test.test_data import \
    get_sch_ticket_data_required, get_send_to_mis_card_data, \
    get_send_to_mis_first_ticket25_data, get_send_to_mis_measures_data, \
    get_send_to_mis_epicrisis_data, get_send_to_mis_second_ticket25_data, \
    get_send_to_mis_pc_ticket25_data
from sirius.blueprints.api.remote_service.tula.passive.childbirth.test.request import \
    create_childbirth, edit_childbirth
from sirius.blueprints.api.remote_service.tula.passive.childbirth.test.test_data import \
    get_childbirth_data_required, get_childbirth_data_more
from sirius.blueprints.api.remote_service.tula.passive.client.test.request import \
    create_client, edit_client
from sirius.blueprints.api.remote_service.tula.passive.client.test.test_data import \
    get_client_data_required, get_client_data_more
from sirius.blueprints.api.remote_service.tula.passive.doctor.test.request import \
    create_doctor, edit_doctor
from sirius.blueprints.api.remote_service.tula.passive.doctor.test.test_data import \
    get_doctor_data_required, get_doctor_data_more
from sirius.blueprints.api.remote_service.tula.passive.hospitalization.test.request import \
    create_hospitalization, edit_hospitalization
from sirius.blueprints.api.remote_service.tula.passive.hospitalization.test.test_data import \
    get_meas_hosp_data_required, get_meas_hosp_data_more
from sirius.blueprints.api.remote_service.tula.passive.organization.test.request import \
    create_organization, edit_organization
from sirius.blueprints.api.remote_service.tula.passive.organization.test.test_data import \
    get_organization_data_required, get_organization_data_more
from sirius.blueprints.api.remote_service.tula.passive.research.test.request import \
    create_research, edit_research
from sirius.blueprints.api.remote_service.tula.passive.research.test.test_data import \
    get_meas_research_data_required, get_meas_research_data_more
from sirius.blueprints.api.remote_service.tula.passive.specialists_checkup.test.request import \
    create_sp_checkup, edit_sp_checkup
from sirius.blueprints.api.remote_service.tula.passive.specialists_checkup.test.test_data import \
    get_sp_checkup_data_required, get_sp_checkup_data_more
from sirius.blueprints.api.test.connect import make_login, release_token

risar_session = None
sirius_session = (None, None)


class _TestTula:

    def test_mr_auth(self):
        global risar_session
        if risar_session:
            return
        with app.app_context():
            with make_login() as sess:
                risar_session = sess
                print 'test_risar_auth', sess

    def test_full_cycle(self, testapp):
        ext_org_id = org_id = 111
        # mis_to_mr_organisation(testapp, ext_org_id)
        ext_doctor_id = doctor_id = 112
        # mis_to_mr_doctor(testapp, ext_org_id, ext_doctor_id)
        ext_client_id = 113
        # mis_to_mr_client(testapp, ext_client_id)
        client_id = 110

        sch_ticket_id = 3928  # 09:00 23.11.16 Тестовый Пользователь (акушер-гинеколог)
        # создать запись на прием в вебе
        # mr_to_mis_sch_ticket(testapp, org_id, doctor_id, client_id, sch_ticket_id)
        # card_id = !mr_create_card(testapp, client_id)
        card_id = 163  # создать карту в вебе
        ext_card_id = 222
        # mr_to_mis_card(testapp, client_id, card_id)
        # !mr_create_first_checkup(testapp, card_id)
        first_checkup_id = 2407  # создать первичный осмотр в вебе
        second_checkup_id = 0  # создать вторичный осмотр в вебе
        pc_checkup_id = 0  # создать осмотр ПЦ в вебе
        # mr_to_mis_first_ticket25(testapp, card_id, first_checkup_id)
        # mr_to_mis_second_ticket25(testapp, card_id, second_checkup_id)
        # mr_to_mis_pc_ticket25(testapp, card_id, pc_checkup_id)
        # создать направления в вебе - осмотр, госпитализация, исследования
        # mr_to_mis_measures(testapp, card_id)
        ext_ch_event_measure_id = 6255  # сразу отсылаем локальные ИД, т.к. пока нет преобразования в builder
        ext_res_event_measure_id = 6258  # сразу отсылаем локальные ИД, т.к. пока нет преобразования в builder

        ext_sp_checkup_id = 114
        # mis_to_mr_meas_sp_checkup(testapp, ext_card_id, ext_org_id, ext_doctor_id,
        #                           ext_ch_event_measure_id, ext_sp_checkup_id)
        # ext_hosp_id = 115
        # mis_to_mr_meas_hosp(testapp, card_id, ext_org_id, ext_doctor_id, event_measure_id, ext_hosp_id)
        ext_research_id = 116
        # mis_to_mr_meas_research(testapp, ext_card_id, ext_org_id, ext_doctor_id,
        #                         ext_res_event_measure_id, ext_research_id)
        # mis_to_mr_first_ticket25
        # mis_to_mr_second_ticket25
        # mis_to_mr_pc_ticket25
        # mis_to_mr_childbirth(testapp, ext_card_id, ext_org_id, ext_doctor_id)

        # mr_to_mis_epicrisis(testapp, card_id)


def mis_to_mr_organisation(testapp, org_id):
    create_organization(testapp, risar_session, get_organization_data_required(org_id))
    # edit_organization(testapp, risar_session, org_id, get_organization_data_more(org_id))


def mis_to_mr_doctor(testapp, org_id, doctor_id):
    create_doctor(testapp, risar_session, get_doctor_data_required(org_id, doctor_id))
    # edit_doctor(testapp, risar_session, org_id, doctor_id, get_doctor_data_more(org_id, doctor_id))


def mis_to_mr_client(testapp, client_id):
    create_client(testapp, risar_session, get_client_data_required(client_id))
    # edit_client(testapp, risar_session, client_id, get_client_data_more(client_id))


def mr_make_appointment(testapp, client_id, ticket_id, doctor_id):
    is_delete = False
    make_appointment(risar_session, get_mr_appointment_data(client_id, ticket_id, doctor_id, is_delete))


def mr_to_mis_sch_ticket(testapp, org_id, doctor_id, client_id, ticket_id):
    is_delete = False
    send_event_remote(testapp, risar_session, get_sch_ticket_data_required(
        is_delete, client_id, ticket_id, org_id, doctor_id
    ))


# def mr_create_card(testapp, client_id, sch_client_ticket_id=None):
#     res = create_card(risar_session, client_id, sch_client_ticket_id)
#     card_id = res['result']['card_id']
#     return card_id


def mr_to_mis_card(testapp, client_id, card_id):
    is_create = True
    request_local(testapp, risar_session, get_send_to_mis_card_data(client_id, card_id, is_create))


# def mr_create_first_checkup(testapp, card_id):
#     res = create_first_checkup(risar_session, card_id, get_first_checkup_data_required())
#     checkup_id = res['result']['checkup_id']
#     return checkup_id


def mr_to_mis_first_ticket25(testapp, card_id, checkup_id):
    is_create = True
    request_local(testapp, risar_session, get_send_to_mis_first_ticket25_data(card_id, checkup_id, is_create))


def mr_to_mis_second_ticket25(testapp, card_id, checkup_id):
    is_create = True
    request_local(testapp, risar_session, get_send_to_mis_second_ticket25_data(card_id, checkup_id, is_create))


def mr_to_mis_pc_ticket25(testapp, card_id, checkup_id):
    is_create = True
    request_local(testapp, risar_session, get_send_to_mis_pc_ticket25_data(card_id, checkup_id, is_create))


def mr_to_mis_measures(testapp, card_id):
    is_create = True
    request_local(testapp, risar_session, get_send_to_mis_measures_data(card_id, is_create))


def mis_to_mr_meas_sp_checkup(testapp, card_id, org_id, doctor_id, event_measure_id, sp_checkup_id):
    create_sp_checkup(testapp, risar_session, card_id, get_sp_checkup_data_required(
        org_id, doctor_id, event_measure_id, sp_checkup_id))
    # edit_sp_checkup(testapp, risar_session, card_id, sp_checkup_id, get_sp_checkup_data_more(
    #     org_id, doctor_id, event_measure_id, sp_checkup_id))


def mis_to_mr_meas_hosp(testapp, card_id, org_id, doctor_id, event_measure_id, meas_hosp_id):
    create_hospitalization(testapp, risar_session, card_id, get_meas_hosp_data_required(
        org_id, doctor_id, event_measure_id, meas_hosp_id))
    edit_hospitalization(testapp, risar_session, card_id, meas_hosp_id, get_meas_hosp_data_more(
        org_id, doctor_id, event_measure_id, meas_hosp_id))


def mis_to_mr_meas_research(testapp, card_id, org_id, doctor_id, event_measure_id, meas_research_id):
    create_research(testapp, risar_session, card_id, get_meas_research_data_required(
        org_id, doctor_id, event_measure_id, meas_research_id))
    # edit_research(testapp, risar_session, card_id, meas_research_id, get_meas_research_data_more(
    #     org_id, doctor_id, event_measure_id, meas_research_id))


def mis_to_mr_childbirth(testapp, card_id, org_id, doctor_id):
    create_childbirth(testapp, risar_session, card_id, get_childbirth_data_required(org_id, doctor_id))
    # edit_childbirth(testapp, risar_session, card_id, get_childbirth_data_more(org_id, doctor_id))


def mr_to_mis_epicrisis(testapp, card_id):
    is_create = False
    request_local(testapp, risar_session, get_send_to_mis_epicrisis_data(card_id, is_create))
