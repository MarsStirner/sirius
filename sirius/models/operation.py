#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class OperationCode(Enum):
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'
    READ_ONE = 'read_one'
    READ_MANY = 'read_many'


class Operation(Model):
    """Операции с сущностями"""

    __tablename__ = 'operation'

    code = Column(db.String(80), unique=False, nullable=False)
