# coding: utf-8


def get_first_ticket25_data_required(org_id, doctor_id, main_id):
    return {
        'external_id': str(main_id),
        'date_open': '2016-12-12',
        'diagnosis': 'A01.1',
        'doctor': str(doctor_id),
        'hospital': str(org_id),
    }


def get_first_ticket25_data_more(org_id, doctor_id, main_id):
    res = get_first_ticket25_data_required(org_id, doctor_id, main_id)
    res.update({
        'date_close': '2016-12-12',
    })
    return res

test_checkup_first_ticket25_data_2 = {
}
