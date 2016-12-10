#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from sirius.blueprints.monitor.exception import InternalError
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.models.system import System
from sqlalchemy import UniqueConstraint, CheckConstraint, text


class Entity(Model):
    """Сущности удаленной и локальной систем"""

    __tablename__ = 'entity'

    code = Column(db.String(80), unique=False, nullable=False)
    system_id = reference_col('system', unique=False, nullable=False)
    system = relationship('System', backref='set_entity')

    __table_args__ = (
        UniqueConstraint('system_id', 'code', name='_sys_entity_uc'),
    )

    @classmethod
    def get_id(cls, system_code, entity_code):
        entity_id = cls.query.join(
            System, System.id == cls.system_id
        ).filter(
            cls.code == entity_code,
            System.code == system_code,
        ).value(cls.id)
        if not entity_id:
            raise InternalError('Entity not exist (%s, %s)' % (system_code, entity_code))
        return entity_id
