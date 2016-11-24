# -*- coding: utf-8 -*-
from sirius.blueprints.api.remote_service.lib.schemas import Schema


class CheckupsTicket25XFormSchema(Schema):
    """
    Схемы для проверки валидности данных талона посещения
    """
    schema = [
        {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "title": "ticket",
            "description": "Талон",
            "type": "object",
            "properties": {
                "external_id": {
                    "description": "Внешний ID",
                    "type": "string"
                },
                "hospital": {
                    "description": "Место обращения (код ЛПУ)",
                    "type": "string"
                },
                "date_open": {
                    "description": "Дата открытия талона",
                    "type": "string",
                    "format": "date"
                },
                "date_close": {
                    "description": "Дата закрытия талона",
                    "type": "string",
                    "format": "date"
                },
                "medical_care": {
                    "description": "Оказываемая медицинская помощь, справочник rbRisarMedicalCare",
                    "type": "string"
                },
                "finished_treatment": {
                    "description": "Обращение (законченный случай лечения), справочник rbRisarFinishedTreatment",
                    "type": "string"
                },
                "initial_treatment": {
                    "description": "Обращение (первичность), справочник rbRisarInitialTreatment",
                    "type": "string"
                },
                "treatment_result": {
                    "description": "Результат обращения, справочник rbResult",
                    "type": "string"
                },
                "payment": {
                    "description": "Оплата за счет, справочник rbFinance",
                    "type": "string"
                },
                "visit_dates": {
                    "description": "Даты посещений",
                    "type": "array",
                    "items": {
                        "type": "string",
                        "format": "date"
                    },
                    "minItems": 1
                },
                "preliminary_diagnosis": {
                    "description": "Диагноз предварительный (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "preliminary_reason": {
                    "description": "Внешняя причина (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "medical_services": {
                    "description": "Медицинские услуги",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "medical_service": {
                                "description": "Медицинская услуга (код)",
                                "type": "string"
                            },
                            "medical_service_doctor": {
                                "description": "Врач, оказавший услугу (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "diagnosis": {
                    "description": "Диагноз заключительный (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "reason": {
                    "description": "Внешняя причина (код МКБ)",
                    "type": "string",
                    "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                },
                "diagnosis_sop": {
                    "description": "Сопутствующие заболевания",
                    "type": "array",
                    "items": {
                        "description": "Сопутствующее заболевание (код МКБ)",
                        "type": "string",
                        "pattern": "^([A-Z][0-9][0-9])(\\.([0-9]{1,2})(\\.[0-9]+)?)?$"
                    }
                },
                "disease_character": {
                    "description": "Заболевание, справочник rbDiseaseCharacter",
                    "type": "string"
                },
                "dispensary": {
                    "description": "Диспансерное наблюдение, справочник rbDispancer",
                    "type": "string"
                },
                "trauma": {
                    "description": "Травма, справочник rbTraumaType",
                    "type": "string"
                },
                "operations": {
                    "description": "Операции",
                    "type": "array",
                    "items": {
                        "description": "Операция",
                        "type": "object",
                        "properties": {
                            "operation_code": {
                                "description": "Операция (код)",
                                "type": "string"
                            },
                            "operation_anesthesia": {
                                "description": "Анестезия, справочник rbRisarOperationAnesthetization",
                                "type": "string"
                            },
                            "operation_equipment": {
                                "description": "Операция проведена с использованием аппаратуры, справочник rbRisarOperationEquipment",
                                "type": "string"
                            },
                            "operation_doctor": {
                                "description": "Врач операции (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "manipulations": {
                    "description": "Манипуляции, исследования",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "manipulation": {
                                "description": "Манипуляция, исследование (код)",
                                "type": "string"
                            },
                            "manipulation_quantity": {
                                "description": "Манипуляция, количество",
                                "type": "integer"
                            },
                            "manipulation_doctor": {
                                "description": "Врач манипуляции (код врача)",
                                "type": "string"
                            }
                        }
                    }
                },
                "sick_leaves": {
                    "description": "Документы о временной нетрудоспособности",
                    "type": "array",
                    "items": {
                        "description": "Документ о временной нетрудоспособности",
                        "type": "object",
                        "properties": {
                            "sick_leave_type": {
                                "description": "Документ о временной нетрудоспособности, справочник rbRisarSickLeaveType",
                                "type": "string"
                            },
                            "sick_leave_reason": {
                                "description": "Повод выдачи, справочник rbRisarSickLeaveReason",
                                "type": "string"
                            },
                            "sick_leave_date_open": {
                                "description": "Дата выдачи",
                                "type": "string",
                                "format": "date"
                            },
                            "sick_leave_date_close": {
                                "description": "Дата закрытия",
                                "type": "string",
                                "format": "date"
                            }
                        }
                    }
                },
                "doctor": {
                    "description": "Врач (код врача)",
                    "type": "string"
                }
            }
        }
    ]
