#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class SystemCode(Enum):
    LOCAL = 'risar'
    TULA = 'tula'
    TAMBOV = 'tambov'


class System(Model):
    """Локальные и удаленные системы"""

    __tablename__ = 'system'

    code = Column(db.String(80), unique=False, nullable=False)
    url = Column(db.String(80), unique=False, nullable=False)  # rename to host
