#! coding:utf-8
"""


@author: BARS Group
@date: 28.09.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.models.entity import Entity
from sirius.models.system import System, SystemCode
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.orm import aliased


class MatchingId(Model):
    """Сопоставление ID частей сущности удаленной и локальной систем"""

    __tablename__ = 'matching_id'

    local_entity_id = reference_col('entity', unique=False, nullable=False)
    local_entity = relationship('Entity', backref='set_local_matching_id',
                                foreign_keys='MatchingId.local_entity_id')
    local_id = Column(db.Integer, unique=False, nullable=False, index=True)
    local_param_name = Column(db.String(80), unique=False, nullable=True)

    remote_entity_id = reference_col('entity', unique=False, nullable=False)
    remote_entity = relationship('Entity', backref='set_remote_matching_id',
                                 foreign_keys='MatchingId.remote_entity_id')
    remote_id = Column(db.String(80), unique=False, nullable=False, index=True)
    remote_param_name = Column(db.String(80), unique=False, nullable=True)

    __table_args__ = (
        UniqueConstraint('local_entity_id', 'local_id', name='_local_entity_id_uc'),
        UniqueConstraint('remote_entity_id', 'remote_id', name='_remote_entity_id_uc'),
        CheckConstraint("local_param_name > '' OR remote_param_name > ''", name='_param_name_chk'),
    )

    @classmethod
    def first_local_id(cls, src_entity_code, src_id, dst_entity_code, remote_sys_code):
        dst_id = None
        dst_param_name = None
        LocalEntity = aliased(Entity, name='LocalEntity')
        LocalSystem = aliased(System, name='LocalSystem')
        RemoteEntity = aliased(Entity, name='RemoteEntity')
        RemoteSystem = aliased(System, name='RemoteSystem')
        res = cls.query.join(
            LocalEntity, LocalEntity.id == cls.local_entity_id
        ).join(
            LocalSystem, LocalSystem.id == LocalEntity.system_id
        ).join(
            RemoteEntity, RemoteEntity.id == cls.remote_entity_id
        ).join(
            RemoteSystem, RemoteSystem.id == RemoteEntity.system_id
        ).filter(
            RemoteEntity.code == src_entity_code,
            RemoteSystem.code == remote_sys_code,
            cls.remote_id == str(src_id),
            LocalEntity.code == dst_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
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
        LocalEntity = aliased(Entity, name='LocalEntity')
        LocalSystem = aliased(System, name='LocalSystem')
        RemoteEntity = aliased(Entity, name='RemoteEntity')
        RemoteSystem = aliased(System, name='RemoteSystem')
        res = cls.query.join(
            LocalEntity, LocalEntity.id == cls.local_entity_id
        ).join(
            LocalSystem, LocalSystem.id == LocalEntity.system_id
        ).join(
            RemoteEntity, RemoteEntity.id == cls.remote_entity_id
        ).join(
            RemoteSystem, RemoteSystem.id == RemoteEntity.system_id
        ).filter(
            LocalEntity.code == src_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.local_id == src_id,
            RemoteEntity.code == dst_entity_code,
            RemoteSystem.code == remote_sys_code,
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
        local_entity_id = Entity.get_id(SystemCode.LOCAL, local_entity_code)
        remote_entity_id = Entity.get_id(remote_sys_code, remote_entity_code)
        cls.create(
            local_entity_id=local_entity_id,
            local_id=local_id,
            local_param_name=local_param_name,
            remote_entity_id=remote_entity_id,
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
        LocalEntity = aliased(Entity, name='LocalEntity')
        LocalSystem = aliased(System, name='LocalSystem')
        RemoteEntity = aliased(Entity, name='RemoteEntity')
        RemoteSystem = aliased(System, name='RemoteSystem')
        rec = cls.query.join(
            LocalEntity, LocalEntity.id == cls.local_entity_id
        ).join(
            LocalSystem, LocalSystem.id == LocalEntity.system_id
        ).join(
            RemoteEntity, RemoteEntity.id == cls.remote_entity_id
        ).join(
            RemoteSystem, RemoteSystem.id == RemoteEntity.system_id
        ).filter(
            RemoteSystem.code == remote_sys_code,
            RemoteEntity.code == remote_entity_code,
            cls.remote_id == str(remote_id),
            LocalSystem.code == SystemCode.LOCAL,
            LocalEntity.code == local_entity_code,
            cls.local_id == local_id,
        ).first()
        rec.delete()


# class MatchingEntity(Model):
#     """Сопоставление сущностей удаленной и локальной систем"""
#
#     __tablename__ = 'matching_entity'
#
#     local_entity_id = reference_col('entity', unique=False, nullable=False)
#     local_entity = relationship('Entity', backref='set_local_matching_entity',
#                                 foreign_keys='MatchingEntity.local_entity_id')
#
#     remote_entity_id = reference_col('entity', unique=False, nullable=False)
#     remote_entity = relationship('Entity', backref='set_remote_matching_entity',
#                                  foreign_keys='MatchingEntity.remote_entity_id')
#
#     is_concomitant = Column(db.Boolean(), unique=False, nullable=False, default=False)
#
#     __table_args__ = (
#         UniqueConstraint('local_entity_id', 'remote_entity_id', name='_local_entity_remote_entity_uc'),
#     )
#
#     @classmethod
#     def get_remote(cls, local_entity_code, remote_sys_code):
#         LocalEntity = aliased(Entity, name='LocalEntity')
#         LocalSystem = aliased(System, name='LocalSystem')
#         RemoteEntity = aliased(Entity, name='RemoteEntity')
#         RemoteSystem = aliased(System, name='RemoteSystem')
#         res = cls.select(RemoteEntity.code).join(
#             LocalEntity, LocalEntity.id == cls.local_entity_id
#         ).join(
#             LocalSystem, LocalSystem.id == LocalEntity.system_id
#         ).join(
#             RemoteEntity, RemoteEntity.id == cls.remote_entity_id
#         ).join(
#             RemoteSystem, RemoteSystem.id == RemoteEntity.system_id
#         ).filter(
#             LocalSystem.code == SystemCode.LOCAL,
#             LocalEntity.code == local_entity_code,
#             RemoteSystem.code == remote_sys_code,
#             cls.is_concomitant == False,
#         )
#         return set(res)
