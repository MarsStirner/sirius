# -*- coding: utf-8 -*-
from sirius.blueprints.api.remote_service.lib.schemas import Schema


class RefbookSchema(Schema):
    """
    Схемы для проверки валидности данных
    """
    schema = [{
        "type": "object",
        "$schema": "http://json-schema.org/draft-04/schema",
        "properties": {
            "code": {
                "id": "refbook/code",
                "type": "string",
                "description": "Код элемента"
            },
            "value": {
                "id": "refbook/value",
                "type": "string",
                "description": "Значение элемента"
            },
        },
        "required": [
            "code",
            "value"
        ]
    }]
