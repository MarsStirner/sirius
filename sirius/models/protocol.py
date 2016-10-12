#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class ProtocolCode(Enum):
    REST = 'rest'
    SOAP = 'soap'


class Protocol(Model):
    """Протоколы передачи данных"""

    __tablename__ = 'protocol'

    code = Column(db.String(80), unique=False, nullable=False)
