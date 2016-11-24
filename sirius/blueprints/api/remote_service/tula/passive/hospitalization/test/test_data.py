# coding: utf-8

def get_meas_hosp_data_required(org_id, doctor_id, event_measure_id, main_id):
    return {
        'external_id': str(main_id),
        'measure_id': str(event_measure_id),
        'measure_type_code': 'hospitalization',
        'hospital': str(org_id),
        'doctor': str(doctor_id),
        'diagnosis_in': 'A1.1',
        'diagnosis_out': 'A1.2',
    }


def get_meas_hosp_data_more(org_id, doctor_id, event_measure_id, main_id):
    res = get_meas_hosp_data_required(org_id, doctor_id, event_measure_id, main_id)
    res.update({
        'status': 'performed',  # rbMeasureStatus
    })
    return res

test_hospitalization_data_2 = {
}
