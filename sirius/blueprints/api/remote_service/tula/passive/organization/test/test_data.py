# coding: utf-8


def get_organization_data_required(main_id):
    return {
        "full_name": "full_cycle_test_org",
        "short_name": "test_org",
        "address": "test_address",
        "area": "64000000000",
        "LPU_id": str(main_id),
        "is_LPU": 1,
    }


def get_organization_data_more(main_id):
    res = get_organization_data_required(main_id)
    res.update({
        "phone": "89008889900",
    })
    return res

test_organization_data_error_1 = {
}
