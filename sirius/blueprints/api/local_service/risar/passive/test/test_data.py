#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""

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
