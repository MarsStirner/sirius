#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


# class LocalQueueCode(Enum):
#     MAIN = 'sir_test_risar_main_queue'
#     ERROR_1 = 'sir_test_risar_error_1_queue'
#     ERROR_2 = 'sir_test_risar_error_2_queue'
#
#
# class Queue(Model):
#     """Очереди удаленной и локальной систем"""
#
#     __tablename__ = 'queue'
#
#     code = Column(db.String(80), unique=False, nullable=False)
#     system_id = reference_col('system', unique=False, nullable=False)
#     system = relationship('System', backref='set_entity')
#
#     __table_args__ = (
#         UniqueConstraint('system_id', 'code', name='_sys_queue_uc'),
#     )
