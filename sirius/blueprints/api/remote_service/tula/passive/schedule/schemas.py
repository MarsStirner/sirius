# -*- coding: utf-8 -*-
from sirius.blueprints.api.remote_service.lib.schemas import Schema


class ScheduleSchema(Schema):
    """
    Схемы для проверки валидности данных организаций и лпу
    """
    schema = [{
        "$schema": "http://json-schema.org/draft-04/schema#",
        "title": "schedule_full",
        "description": "Расписание полное (рабочий промежуток, слоты, записи на прием)",
        "type": "object",
        "properties": {
            "schedule_id": {
                "description": "id рабочего промежутка",
                "type": "string"
            },
            "hospital": {
                "description": "ЛПУ (код)",
                "type": "string"
            },
            "doctor": {
                "description": "Врач (код)",
                "type": "string"
            },
            "date": {
                "description": "Дата",
                "type": "string",
                "format": "date"
            },
            "time_begin": {
                "description": "Время начала промежутка",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "time_end": {
                "description": "Время завершения промежутка",
                "type": "string",
                "pattern": "^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"
            },
            "quantity": {
                "description": "Запланированное количество приемов в интервале",
                "type": "integer"
            },
            "quota_type": {
                "description": "Тип квоты",
                "type": "string"
            },
            "appointment_permited": {
                "description": "Разрешена запись на прием",
                "type": "boolean"
            },
            "schedule_tickets": {
                "description": "Список слотов расписания",
                "type": "array",
                "items": {
                    "description": "Слот расписания",
                    "type": "object",
                    "properties": {
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
                        "patient": {
                            "description": "Пациент (id пациента)",
                            "type": "string"
                        },
                        "schedule_ticket_type": {
                            "description": "Тип записи на прием",
                            "type": "string"
                        },
                        "schedule_ticket_id": {
                            "description": "id записи на прием",
                            "type": "string"
                        }
                     },
                    "required": ["schedule_ticket_type"]
                },
                "minItems": 0
            }
        },
        "required": ["hospital","doctor","date","time_begin","time_end","quota_type"]
    }]
