# -*- coding: utf-8 -*-
from sirius.blueprints.api.remote_service.lib.schemas import Schema


class HospitalizationSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "hospitalization",
            "description": "Госпитализация",
            "type": "object",
            "properties": {
                "result_action_id": {
                    "description": "ID Action с результатами госпитализации",
                    "type": "string"
                },
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "measure_id": {
                    "description": "ID мероприятия случая",
                    "type": "string"
                },
                "date_in": {
                    "description": "Дата поступленияя",
                    "type": "string",
                    "format": "date"
                },
                "date_out": {
                    "description": "Дата выписки",
                    "type": "string",
                    "format": "date"
                },
                "hospital": {
                    "description": "ЛПУ (код)",
                    "type": "string"
                },
                "doctor": {
                    "description": "Лечащий врач (код)",
                    "type": "string"
                },
                "pregnancy_week": {
                    "description": "Срок беременности при поступлении (недель)",
                    "type": "integer"
                },
                "diagnosis_in": {
                    "description": "Диагноз при поступлении",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "diagnosis_out": {
                    "description": "Диагноз при выписке",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "results": {
                    "type": "string",
                    "description": "Результаты госпитализации"
                },
                "status": {
                    "description": "Статус мероприятия, справочник rbMeasureStatus",
                    "type": "string"
                }
            },
            "required": ["hospital", "doctor", "diagnosis_in", "diagnosis_out"]
        },
    ]
