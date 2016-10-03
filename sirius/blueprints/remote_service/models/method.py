#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint


class ApiMethod(Model):
    """Сопоставление ID частей сущности удаленной и локальной систем"""

    __tablename__ = 'api_method'

    entity_code = Column(db.String(80), unique=False, nullable=False)
    operation_code = Column(db.String(80), unique=False, nullable=False)
    system_code = Column(db.String(80), unique=False, nullable=False)
    method = Column(db.String(80), unique=False, nullable=False)
    template_url = Column(db.Text(), unique=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('entity_code', 'operation_code', 'system_code', name='_entity_operation_system_uc'),
    )

    @classmethod
    def get_method(cls, entity_code, operation_code, system_code):
        method = cls.query.filter(
            cls.entity_code == entity_code,
            cls.operation_code == operation_code,
            cls.system_code == system_code,
        ).first()
        if not method:
            raise RuntimeError('Service not found')
        res = {
            'method': method.method,
            'template_url': method.template_url,
        }
        return res
