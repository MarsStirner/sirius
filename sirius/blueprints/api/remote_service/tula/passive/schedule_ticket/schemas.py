# -*- coding: utf-8 -*-
from sirius.blueprints.api.remote_service.lib.schemas import Schema


class ScheduleTicketSchema(Schema):
    """
    Схемы для проверки валидности данных организаций и лпу
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule_tickets",
        "description": "Запись на прием",
        "type": "object",
        "properties": {
            "schedule_id": {
                "description": "id рабочего промежутка",
                "type": "string"
            },
            "schedule_time_begin": {
                "description": "Время начала промежутка",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "schedule_ticket_id": {
                "description": "id записи на прием",
                "type": "string"
            },
            "hospital": {
                "description": "ЛПУ (код ЛПУ)",
                "type": "string"
            },
            "doctor": {
                "description": "Врач (код врача)",
                "type": "string"
            },
            "patient": {
                "description": "Пациент (id пациента)",
                "type": "string"
            },
            "date": {
                "description": "Дата приема",
                "type": "string",
                "format": "date"
            },
            "time_begin": {
                "description": "Время приема",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "time_end": {
                "description": "Время приема",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "schedule_ticket_type": {
                "description": "Тип записи на прием",
                "type": "string"
            }
        },
        "required": ["hospital","doctor","patient","date","schedule_ticket_type"]
    }]
