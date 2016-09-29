#! coding:utf-8
"""


@author: BARS Group
@date: 28.09.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship


class Conformity(Model):
    """Сопоставление ID частей сущности удаленной и локальной систем"""

    __tablename__ = 'conformity'
    name = Column(db.String(80), unique=True, nullable=False)
    user_id = reference_col('users', nullable=True)
    user = relationship('User', backref='conformity_set')

    local_id = Column(db.Integer, unique=False, nullable=True)
    part_name = Column(db.String(80), unique=True, nullable=False)

    remote_id = Column(db.Integer, unique=False, nullable=True)
