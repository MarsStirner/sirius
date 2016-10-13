#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB


class Entity(Model):
    """Сущности удаленной и локальной систем"""

    __tablename__ = 'entity'

    code = Column(db.String(80), unique=False, nullable=False)
    system_id = reference_col('system', unique=False, nullable=False)
    system = relationship('System', backref='set_entity')

    __table_args__ = (
        UniqueConstraint('system_id', 'code', name='_sys_entity_uc'),
    )


class EntityImage(Model):
    """Отпечаток содержимого сущностей удаленных систем"""

    __tablename__ = 'entity_image'

    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_entity_image')
    parent_id = reference_col('entity_image', unique=False, nullable=True)
    parent = relationship('EntityImage')
    external_id = Column(db.Integer, unique=False, nullable=False)
    content = Column(JSONB, unique=False, nullable=False)
