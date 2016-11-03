#! coding:utf-8
"""


@author: BARS Group
@date: 25.10.2016

"""

request_tula_patient_1 = {
    "remote_system_code": 'tambov',
    "remote_entity_code": 'patient',
    "remote_main_id": '6EHBT7UCLVXB5LSV',
}

request_tula_register_patient_card = {
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

request_risar_first_checkup_1995 = {
    'service_method': 'api_checkup_obs_first_ticket25_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/127/checkup/obs/first/1995/ticket25',
    'request_method': 'get',
    'request_params': {'card_id': 127},
    'main_id': 1995,
    'main_param_name': 'exam_obs_id',
    'method': 'post' if False else 'put',
}

request_risar_measures_127 = {
    'service_method': 'api_measure_list_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/127/measures/list/',
    'request_method': 'get',
    'request_params': {'card_id': 127},
    'main_id': None,
    'main_param_name': None,
    'method': 'post' if False else 'put',
}

request_risar_second_checkup_1995 = {
    'service_method': 'api_checkup_obs_second_ticket25_get',
    'request_url': 'http://localhost:6600/risar/api/integration/0/card/127/checkup/obs/second/1995/ticket25',
    'request_method': 'get',
    'request_params': {'card_id': 127},
    'main_id': 1995,
    'main_param_name': 'exam_obs_id',
    'method': 'post' if False else 'put',
}
