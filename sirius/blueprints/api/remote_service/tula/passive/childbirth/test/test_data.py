# coding: utf-8

def get_childbirth_data_required(org_id, doctor_id):
    return {
        'general_info': {
            'admission_date': '2016-12-12',
            'pregnancy_duration': 48,
            'delivery_date': '2016-12-12',
            'delivery_time': '11:00',
            'maternity_hospital': str(org_id),
            'maternity_hospital_doctor': str(doctor_id),
            'diagnosis_osn': 'A01.1',
            'pregnancy_final': 'rodami',  # rbRisarPregnancy_Final
        },
        'kids': []
    }


def get_childbirth_data_more(org_id, doctor_id):
    res = get_childbirth_data_required(org_id, doctor_id)
    res.update({
        'operations': {
            'caesarean_section': 'korporal_noe',  # rbRisarCaesarean_Section
        }
    })
    return res

test_childbirth_data_2 = {
}
