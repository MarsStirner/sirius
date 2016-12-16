#! coding:utf-8
"""


@author: BARS Group
@date: 28.09.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.models.entity import Entity
from sirius.models.system import System, SystemCode
from sqlalchemy import UniqueConstraint, CheckConstraint, text
from sqlalchemy.orm import aliased


class MatchingId(Model):
    """Сопоставление ID частей сущности удаленной и локальной систем"""

    __tablename__ = 'matching_id'

    local_entity_id = reference_col('entity', unique=False, nullable=False)
    local_entity = relationship('Entity', backref='set_local_matching_id',
                                foreign_keys='MatchingId.local_entity_id')
    local_id_prefix = Column(db.String(80), unique=False, nullable=False, index=False, server_default='')
    local_id = Column(db.String(80), unique=False, nullable=False, index=True)
    local_param_name = Column(db.String(80), unique=False, nullable=True)

    remote_entity_id = reference_col('entity', unique=False, nullable=False)
    remote_entity = relationship('Entity', backref='set_remote_matching_id',
                                 foreign_keys='MatchingId.remote_entity_id')
    remote_id_prefix = Column(db.String(80), unique=False, nullable=False, index=False, server_default='')
    remote_id = Column(db.String(80), unique=False, nullable=False, index=True)
    remote_param_name = Column(db.String(80), unique=False, nullable=True)
    created = Column(db.DateTime, unique=False, nullable=False, server_default=text('now()'))

    __table_args__ = (
        UniqueConstraint(
            'local_entity_id', 'local_id', 'local_id_prefix', 'remote_entity_id',
            name='_local_entity_local_id_loc_id_pref_remote_entity_uc'
        ),
        UniqueConstraint(
            'remote_entity_id', 'remote_id', 'remote_id_prefix', 'local_entity_id',
            name='_remote_entity_remote_id_rem_id_pref_local_entity_uc'
        ),
        CheckConstraint("local_param_name > '' OR remote_param_name > ''", name='_param_name_chk'),
    )

    @classmethod
    def first_local_id(cls, remote_entity_code, remote_id,
                       local_entity_code, remote_sys_code, remote_id_prefix=None):
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
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
            cls.remote_id == str(remote_id),
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
        )
        if remote_id_prefix:
            res = res.filter(
                cls.remote_id_prefix == (remote_id_prefix or ''),
            )
        res = res.first()
        if res:
            dst_id = res.local_id
            dst_param_name = res.local_param_name
        res = {
            'dst_id': dst_id,
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def first_remote_id(cls, src_entity_code, src_id, dst_entity_code,
                        remote_sys_code, src_id_prefix=None):
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
            cls.local_id == str(src_id),
            RemoteEntity.code == dst_entity_code,
            RemoteSystem.code == remote_sys_code,
        )
        if src_id_prefix:
            res = res.filter(
                cls.local_id_prefix == (src_id_prefix or ''),
            )
        res = res.first()
        if res:
            dst_id = res.remote_id
            dst_param_name = res.remote_param_name
        res = {
            'dst_id': dst_id,
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def shortest_first_remote_id(cls, src_entity_code, src_id, remote_sys_code, src_id_prefix=None):
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
            cls.local_id == str(src_id),
            RemoteSystem.code == remote_sys_code,
        )
        if src_id_prefix:
            res = res.filter(
                cls.local_id_prefix == (src_id_prefix or ''),
            )
        res = res.first()
        if res:
            dst_id = res.remote_id
            dst_param_name = res.remote_param_name
        res = {
            'dst_id': dst_id,
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def first_remote_param_name(cls, remote_entity_code, remote_id, remote_sys_code, remote_id_prefix=None):
        dst_param_name = None
        RemoteEntity = aliased(Entity, name='RemoteEntity')
        RemoteSystem = aliased(System, name='RemoteSystem')
        res = cls.query.join(
            RemoteEntity, RemoteEntity.id == cls.remote_entity_id
        ).join(
            RemoteSystem, RemoteSystem.id == RemoteEntity.system_id
        ).filter(
            cls.remote_id == str(remote_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        )
        if remote_id_prefix:
            res = res.filter(
                cls.remote_id_prefix == (remote_id_prefix or ''),
            )
        res = res.first()
        if res:
            dst_param_name = res.remote_param_name
        res = {
            'dst_id_url_param_name': dst_param_name,
        }
        return res

    @classmethod
    def get_local_id(cls, local_entity_code, remote_entity_code, remote_id, remote_sys_code, remote_id_prefix=None):
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
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.remote_id == str(remote_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        )
        if remote_id_prefix:
            res = res.filter(
                cls.remote_id_prefix == (remote_id_prefix or ''),
            )
        res = res.one()
        return res.local_id

    @classmethod
    def find_local_id(cls, local_entity_code, remote_entity_code, remote_id, remote_sys_code, remote_id_prefix=None):
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
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.remote_id == str(remote_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        )
        if remote_id_prefix:
            res = res.filter(
                cls.remote_id_prefix == (remote_id_prefix or ''),
            )
        res = res.first()
        return res and res.local_id

    @classmethod
    def get_remote_id(cls, local_entity_code, local_id, remote_entity_code, remote_sys_code, local_id_prefix=None):
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
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.local_id == str(local_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        )
        if local_id_prefix:
            res = res.filter(
                cls.local_id_prefix == (local_id_prefix or ''),
            )
        res = res.one()
        return res.remote_id

    @classmethod
    def first_by_remote_id_without_prefix(cls, local_entity_code, remote_entity_code, remote_id, remote_sys_code):
        # специальный для обновления филиала врача в Туле
        # по хорошему филиал обновлять при синхронизации врачей (но долго)
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
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.remote_id == str(remote_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        ).first()
        return res

    @classmethod
    def get_remote_prefix_id(cls, local_entity_code, remote_entity_code, remote_id, remote_sys_code):
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
            LocalEntity.code == local_entity_code,
            LocalSystem.code == SystemCode.LOCAL,
            cls.remote_id == str(remote_id),
            RemoteEntity.code == remote_entity_code,
            RemoteSystem.code == remote_sys_code,
        ).one()
        return res.remote_id_prefix

    @classmethod
    def add(
        cls,
        local_entity_id=None,
        local_id_prefix=None,
        local_id=None,
        local_param_name=None,
        remote_entity_id=None,
        remote_id_prefix=None,
        remote_id=None,
        remote_param_name=None,
    ):
        cls.create(
            local_entity_id=local_entity_id,
            local_id_prefix=local_id_prefix or '',
            local_id=local_id,
            local_param_name=local_param_name,
            remote_entity_id=remote_entity_id,
            remote_id_prefix=remote_id_prefix or '',
            remote_id=remote_id,
            remote_param_name=remote_param_name,
        )

    @classmethod
    def remove(
        cls,
        remote_sys_code=None,
        remote_entity_code=None,
        remote_id_prefix=None,
        remote_id=None,
        local_entity_code=None,
        local_id_prefix=None,
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
            cls.remote_id_prefix == (remote_id_prefix or ''),
            cls.remote_id == str(remote_id),
            LocalSystem.code == SystemCode.LOCAL,
            LocalEntity.code == local_entity_code,
            cls.local_id_prefix == (local_id_prefix or ''),
            cls.local_id == str(local_id),
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
