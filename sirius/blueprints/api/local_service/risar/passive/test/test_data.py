#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""
from sirius.blueprints.api.local_service.risar.events import RisarEvents

request_tambov_patient_1 = {
    "remote_system_code": 'tambov',
    "remote_entity_code": 'patient',
    "remote_main_id": '6EHBT7UCLVXB5LSV',
}

request_tambov_register_patient_card = {
    "local_main_id": None,
    "remote_system_code": 'tambov',
    "remote_entity_code": 'patient',
    "remote_main_id": '6EHBT7UCLVXB5LSV',
}

create_risar_card_1 = {
    'client_id': None,
    'card_set_date': '2016-11-02',
    'card_doctor': '995',
    'card_LPU': '1246'
}

request_risar_first_checkup_2159 = {
    'service_method': 'api_checkup_obs_first_ticket25_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/139/checkup/obs/first/2159/ticket25',
    'request_method': 'get',
    'request_params': {'card_id': 139},
    'main_id': 2159,
    'main_param_name': 'exam_obs_id',
    'method': 'post' if False else 'put',
}

request_risar_measures_139 = {
    'service_method': 'api_measure_list_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/139/measures/list/',
    'request_method': 'get',
    'request_params': {'card_id': 139},
    'main_id': None,
    'main_param_name': None,
    'method': 'post' if False else 'put',
}

request_risar_second_checkup_2159 = {
    'service_method': 'api_checkup_obs_second_ticket25_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/139/checkup/obs/second/2159/ticket25',
    'request_method': 'get',
    'request_params': {'card_id': 139},
    'main_id': 2159,
    'main_param_name': 'exam_obs_id',
    'method': 'post' if False else 'put',
}


def get_request_risar_get_measure_research(card_id, main_id):
    request_risar_get_measure_research = {
        'service_method': 'api_measure_get',
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/measures/%s' % (card_id, main_id),
        'request_method': 'get',
        'request_params': {'card_id': card_id},
        'main_id': main_id,
        'main_param_name': 'measure_id',
        'method': 'get',
    }
    return request_risar_get_measure_research


def get_sch_ticket_data_required(is_delete, client_id, ticket_id, org_id, doctor_id):
    return {
        'event': RisarEvents.MAKE_APPOINTMENT,
        'method': 'delete' if is_delete else 'post',
        "service_method": 'api_schedule_tickets_get',
        "request_params": {'client_id': client_id},
        "main_id": ticket_id,
        "main_param_name": 'schedule_ticket_id',
        "data": {
            "hospital": str(org_id),
            "doctor": str(doctor_id),
            "date": '2016-12-12',
            "time": '11:00:00'[:5],
        }
    }


def get_send_to_mis_card_data(client_id, card_id, is_create):
    return {
        'service_method': 'risar.api_card_get',
        'request_method': 'get',
        'main_param_name': 'card_id',
        'request_params': {'client_id': client_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s?client_id=%s' %
                       (str(card_id), str(client_id)),
        'event': RisarEvents.CREATE_CARD,
        'main_id': card_id,
        'method': 'post' if is_create else 'put',
    }


def get_send_to_mis_first_ticket25_data(card_id, checkup_id, is_create):
    return {
        'service_method': 'risar.api_checkup_obs_first_ticket25_get',
        'request_method': 'get',
        'main_param_name': 'external_id',
        'request_params': {'card_id': card_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/checkup/obs/first/%s/ticket25' % (card_id, checkup_id),
        'event': RisarEvents.SAVE_CHECKUP,
        'main_id': checkup_id,
        'method': 'post' if is_create else 'put',
    }


def get_send_to_mis_second_ticket25_data(card_id, checkup_id, is_create):
    return {
        'service_method': 'risar.api_checkup_obs_second_ticket25_get',
        'request_method': 'get',
        'main_param_name': 'external_id',
        'request_params': {'card_id': card_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/checkup/obs/second/%s/ticket25' % (card_id, checkup_id),
        'event': RisarEvents.SAVE_CHECKUP,
        'main_id': checkup_id,
        'method': 'post' if is_create else 'put',
    }


def get_send_to_mis_pc_ticket25_data(card_id, checkup_id, is_create):
    return {
        'service_method': 'risar.api_checkup_pc_ticket25_get',
        'request_method': 'get',
        'main_param_name': 'external_id',
        'request_params': {'card_id': card_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/checkup/pc/%s/ticket25' % (card_id, checkup_id),
        'event': RisarEvents.SAVE_CHECKUP,
        'main_id': checkup_id,
        'method': 'post' if is_create else 'put',
    }


def get_send_to_mis_measures_data(card_id, is_create):
    return {
        'service_method': 'risar.api_measure_list_get',
        'request_method': 'get',
        'main_param_name': 'card_id',
        'request_params': {'card_id': card_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/measures/list/' % card_id,
        'event': RisarEvents.SAVE_CHECKUP,
        'main_id': card_id,
        'method': 'post' if is_create else 'put',
    }


def get_send_to_mis_epicrisis_data(card_id, is_create):
    return {
        'service_method': 'risar.api_integr_epicrisis_get',
        'request_method': 'get',
        'main_param_name': 'card_id',
        'request_params': {'card_id': card_id},
        'request_url': 'http://localhost:6600/risar/api/integration/0/card/%s/epicrisis/' % card_id,
        'event': RisarEvents.CLOSE_CARD,
        'main_id': card_id,
        'method': 'post' if is_create else 'put',
    }
