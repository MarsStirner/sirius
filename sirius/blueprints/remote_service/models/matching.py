#! coding:utf-8
"""


@author: BARS Group
@date: 28.09.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sqlalchemy import UniqueConstraint, CheckConstraint


class MatchingId(Model):
    """Сопоставление ID частей сущности удаленной и локальной систем"""

    __tablename__ = 'matching_id'

    local_entity_code = Column(db.String(80), unique=False, nullable=False)
    local_id = Column(db.Integer, unique=False, nullable=False)
    local_param_name = Column(db.String(80), unique=False, nullable=True)

    remote_sys_code = Column(db.String(80), unique=False, nullable=False)
    remote_entity_code = Column(db.String(80), unique=False, nullable=False)
    remote_id = Column(db.Integer, unique=False, nullable=False)
    remote_param_name = Column(db.String(80), unique=False, nullable=True)

    __table_args__ = (
        UniqueConstraint('local_entity_code', 'local_id', name='_local_entity_id_uc'),
        UniqueConstraint('remote_sys_code', 'remote_entity_code', 'remote_id', name='_remote_sys_entity_id_uc'),
        CheckConstraint("local_param_name > '' OR remote_param_name > ''", name='_param_name_chk'),
    )

    @classmethod
    def first_local_id(cls, src_entity_code, src_id, dst_entity_code, remote_sys_code):
        dst_id = None
        dst_param_name = None
        res = cls.query.filter_by(
            remote_entity_code=src_entity_code,
            remote_id=src_id,
            local_entity_code=dst_entity_code,
            remote_sys_code=remote_sys_code,
        ).first()
        if res:
            dst_id = res.local_id
            dst_param_name = res.local_param_name
        res = {
            'dst_id': dst_id,
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def first_remote_id(cls, src_entity_code, src_id, dst_entity_code, remote_sys_code):
        dst_id = None
        dst_param_name = None
        res = cls.query.filter_by(
            local_entity_code=src_entity_code,
            local_id=src_id,
            remote_entity_code=dst_entity_code,
            remote_sys_code=remote_sys_code,
        ).first()
        if res:
            dst_id = res.remote_id
            dst_param_name = res.remote_param_name
        res = {
            'dst_id': dst_id,
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def add(
        cls,
        local_entity_code=None,
        local_id=None,
        local_param_name=None,
        remote_sys_code=None,
        remote_entity_code=None,
        remote_id=None,
        remote_param_name=None,
    ):
        cls.create(
            local_entity_code=local_entity_code,
            local_id=local_id,
            local_param_name=local_param_name,
            remote_sys_code=remote_sys_code,
            remote_entity_code=remote_entity_code,
            remote_id=remote_id,
            remote_param_name=remote_param_name,
        )

    @classmethod
    def remove(
        cls,
        remote_sys_code=None,
        remote_entity_code=None,
        remote_id=None,
        local_entity_code=None,
        local_id=None,
    ):
        rec = cls.query.filter_by(
            remote_sys_code=remote_sys_code,
            remote_entity_code=remote_entity_code,
            remote_id=remote_id,
            local_entity_code=local_entity_code,
            local_id=local_id,
        ).first()
        rec.delete()
