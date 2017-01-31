# coding: utf-8


def get_schedule_data_required(main_id, org_id, doctor_id, quota_type, time_begin, schedule_tickets_ids):
    res = {
        'schedule_id': str(main_id),
        'hospital': str(org_id),
        'doctor': str(doctor_id),
        'date': '2017-01-19',
        'time_begin': '%02d:00' % time_begin,
        'time_end': '%02d:00' % (time_begin + 1),
        'quota_type': str(quota_type),
        'appointment_permited': True,
    }
    for i, schedule_ticket_id in enumerate(schedule_tickets_ids):
        res.setdefault('schedule_tickets', []).append({
            'time_begin': '%02d:%02d' % (time_begin, i * 10),
            'time_end': '%02d:%02d' % (time_begin, (i + 1) * 10),
            'schedule_ticket_type': '0',
            'schedule_ticket_id': str(schedule_ticket_id),
        })
    return res


def get_schedule_data_more(main_id, org_id, doctor_id, quota_type, time_begin, schedule_tickets_ids):
    res = get_schedule_data_required(main_id, org_id, doctor_id, quota_type, time_begin, schedule_tickets_ids)
    res.update({
    })
    return res
