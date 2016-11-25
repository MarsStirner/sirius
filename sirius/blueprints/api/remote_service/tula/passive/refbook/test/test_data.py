# coding: utf-8


def get_refbook_data_required(main_id):
    return {
        'code': str(main_id),
        'value': 'value_01',
    }


def get_refbook_data_changed(main_id):
    return {
        'code': str(main_id),
        'value': 'value_02',
    }
