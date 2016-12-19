# coding: utf-8


def get_org_department_data_required(org_code, main_id):
    return {
        "organisation_id": str(org_code),
        "name": "test_org",
        "address": "test_address",
        "regionalCode": str(main_id),
    }


def get_org_department_data_more(main_id):
    res = get_org_department_data_required(main_id)
    res.update({
        "TFOMSCode": "234234",
    })
    return res

test_org_department_data_error_1 = {
}
