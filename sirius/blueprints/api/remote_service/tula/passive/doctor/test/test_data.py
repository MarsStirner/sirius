# coding: utf-8


def get_doctor_data_required(parent_id, main_id):
    return {
        'last_name': 'full_cycle_test_doctor',
        'first_name': 'test_doctor',
        'sex': 1,
        'SNILS': '654-789-654',
        'INN': '98765432145',
        'organization': str(parent_id),
        'speciality': '44',  # rbSpeciality
        'post': '3',  # rbPost
        'regional_code': str(main_id),

        'login': 'full_cycle',
        'birth_date': '1970-01-01',
    }


def get_doctor_data_more(parent_id, main_id):
    res = get_doctor_data_required(parent_id, main_id)
    res.update({
        'patr_name': 'tdoctor',
    })
    return res

test_doctor_data_error_1 = {
}
