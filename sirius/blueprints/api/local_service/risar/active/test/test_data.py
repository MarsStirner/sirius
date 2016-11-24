#! coding:utf-8
"""


@author: BARS Group
@date: 22.11.2016

"""


def get_mr_appointment_data(client_id, ticket_id, doctor_id, is_delete):
    return {
        'client_id': client_id,
        'ticket_id': ticket_id,
        # 'create_person': doctor_id,
        'appointment_type_id': 1,  # rbAppointmentType
        'event_id': None,
        'delete': is_delete,
        # 'note': '',
    }
