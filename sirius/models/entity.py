#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class LocalEntityCode(Enum):
    CLIENT = 'client'
    CHECKUP_OBS_FIRST = 'checkup_obs_first'


class Entity(Model):
    """Сущности удаленной и локальной систем"""

    __tablename__ = 'entity'

    code = Column(db.String(80), unique=False, nullable=False)
    system_id = reference_col('system', unique=False, nullable=False)
    system = relationship('System', backref='set_entity')

    __table_args__ = (
        UniqueConstraint('system_id', 'code', name='_sys_entity_uc'),
    )
