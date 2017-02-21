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
        "operations": {
            "hysterectomy": "boleedvuhsutokposlerodov",
            "obstetrical_forceps": "polostnye",
            "anesthetization": "990251995",
            "complications": ["A00.1"],
            "caesarean_section": "korporal_noe",
            "specialities": "kogdaproizvodilas_operazia",
            "indication": "990251970",
        },
        "kids": [
            {
                "diseases": [], "weight": 12.0,
                "alive": True,
                "length": 1.0, "maturity_rate": "perenosennyj",
                "date": "2017-02-24",
                "time": "10:00",
                "sex": 1,
            }
        ],
        "childbirth_id": 4348,
        "manipulations": {
            "perineotomy": "wsfd",
        },
        "complications": {
            "pathological_preliminary_period": True,
            "perineal_tear": "02",
            "afterbirth": "polnoeprirasenieplazenty",
            "weakness": "pervicnaa",
            "pre_birth_delivery_waters": True,
            "delivery_waters": "prejdevremennye",
            "funiculus": "korotkaapupovina",
            "eclampsia": "eklampsia",
            "chorioamnionitis": True
        },
        "general_info": {
            "delivery_time": "11:00",
            "diagnosis_osn": "A01.1",
            "pregnancy_duration": 22,
            "curation_hospital": "710046",
            "admission_date": "2017-02-23",
            "maternity_hospital_doctor": "112",
            "maternity_hospital": "111",
            "pregnancy_final": "rodami",
            "delivery_date": "2017-02-23"
        },
    })
    return res

test_childbirth_data_2 = {
}
