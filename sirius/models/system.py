#! coding:utf-8
"""
Регион
  \ МИС - Сущность - Сопоставление
      \ Хост    -\ Метод

@author: BARS Group
@date: 10.10.2016

"""
from hitsl_utils.enum import Enum
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class RegionCode(Enum):
    TULA = 'tula'
    TAMBOV = 'tambov'


class SystemCode(Enum):
    LOCAL = 'risar'
    TULA = 'tula_gr_1'  # тульская интеграционная группа 1
    TAMBOV = 'tambov_gr_1'  # тамбовская интеграционная группа 1


# class Region(Model):
#     """Регионы"""
#
#     __tablename__ = 'region'
#
#     code = Column(db.String(80), unique=True, nullable=False)


class System(Model):
    """Локальные и удаленные системы (РМИС/МР)"""

    __tablename__ = 'system'

    code = Column(db.String(80), unique=False, nullable=False)
    # region_id = reference_col('region', unique=False, nullable=False)
    # region = relationship('Region', backref='set_system')
    #
    # __table_args__ = (
    #     UniqueConstraint('code', 'region_id', name='_system_uc'),
    # )


class Host(Model):
    """Хосты системы"""

    __tablename__ = 'host'

    code = Column(db.String(80), unique=False, nullable=False)
    system_id = reference_col('system', unique=False, nullable=False)
    system = relationship('System', backref='set_host')
    url = Column(db.String(80), unique=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('code', 'system_id', name='_host_uc'),
    )
