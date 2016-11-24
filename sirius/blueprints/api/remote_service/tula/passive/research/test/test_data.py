# coding: utf-8

def get_meas_research_data_required(org_id, doctor_id, event_measure_id, main_id):
    return {
        'external_id': str(main_id),
        'measure_id': str(event_measure_id),
        'measure_type_code': 'func_test',
        'realization_date': '2016-12-12',
        'results': 'p1:1;p2:2',
        'doctor_code': str(doctor_id),
        'lpu_code': str(org_id),
    }


def get_meas_research_data_more(org_id, doctor_id, event_measure_id, main_id):
    res = get_meas_research_data_required(org_id, doctor_id, event_measure_id, main_id)
    res.update({
        'status': 'performed',  # rbMeasureStatus
    })
    return res

test_research_data_2 = {
}
