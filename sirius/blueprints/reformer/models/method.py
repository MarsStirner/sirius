#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
from sirius.blueprints.monitor.exception import InternalError
from sirius.database import Column, Model, db, reference_col, relationship, \
    XMLType
from sirius.models.entity import Entity
from sirius.models.operation import Operation
from sirius.models.protocol import Protocol, ProtocolCode
from sirius.models.system import System
from sqlalchemy import UniqueConstraint, CheckConstraint

# todo: 1. разделить хранение разных протоколов,
# todo: 2. связать ServiceMethod и ApiMethod для rest (переименовать)


class ApiMethod(Model):
    """API метод"""

    __tablename__ = 'api_method'

    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_api_method')
    protocol_id = reference_col('protocol', unique=False, nullable=False)
    protocol = relationship('Protocol', backref='set_api_method')
    method = Column(db.String(80), unique=False, nullable=False)  # service method/rest method
    template_url = Column(db.Text(), unique=False, nullable=False)  # wsdl uri/rest url template
    version = Column(db.Integer, unique=False, nullable=False, server_default='0')

    __table_args__ = (
        # CheckConstraint("protocol_code = '%s' OR wsdl_uri > ''" % ProtocolCode.REST, name='_wsdl_uri_chk'),
    )

    @classmethod
    def get(cls, system_code, entity_code, operation_code, version):
        method = cls.query.join(
            Entity, Entity.id == cls.entity_id
        ).join(
            System, System.id == Entity.system_id
        ).join(
            Protocol, Protocol.id == cls.protocol_id
        ).join(
            ApiMethodOperation, ApiMethodOperation.api_method_id == cls.id
        ).join(
            Operation, Operation.id == ApiMethodOperation.operation_id
        ).filter(
            Entity.code == entity_code,
            Operation.code == operation_code,
            System.code == system_code,
            ApiMethod.version == version,
        ).first()
        if not method:
            raise InternalError('Method not registered in %s' % cls.__name__)
        params_entities = ApiMethodURLParamEntity.get(method.id)
        sys_url = method.entity.system.host.rstrip('/')
        res = {
            'protocol': method.protocol.code,
            'method': method.method,
            'template_url': sys_url + method.template_url,
            'params_entities': params_entities,
        }
        return res


class ApiMethodOperation(Model):
    """Операция метода"""

    __tablename__ = 'api_method_operation'

    api_method_id = reference_col('api_method', unique=False, nullable=False)
    api_method = relationship('ApiMethod', backref='set_method_operation')
    operation_id = reference_col('operation', unique=False, nullable=False)
    operation = relationship('Operation', backref='set_api_method')

    __table_args__ = (
        UniqueConstraint('api_method_id', 'operation_id', name='_api_method_operation_uc'),
    )


class ApiMethodURLParamEntity(Model):
    """Сущность параметра url (для rest)"""

    __tablename__ = 'api_method_url_param_entity'

    api_method_id = reference_col('api_method', unique=False, nullable=False)
    api_method = relationship('ApiMethod', backref='set_url_param_entity')
    param_name = Column(db.String(80), unique=False, nullable=False)
    param_position = Column(db.Integer, unique=False, nullable=False)
    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_url_param_entity')

    __table_args__ = (
        UniqueConstraint('api_method_id', 'param_position', name='_api_method_position_uc'),
        UniqueConstraint('api_method_id', 'entity_id', name='_api_method_entity_id_uc'),
    )

    @classmethod
    def get(cls, api_method_id):
        params = cls.query.join(
            Entity, Entity.id == cls.entity_id
        ).filter(
            cls.api_method_id == api_method_id,
        ).order_by(cls.param_position).all()
        res = [rec.entity.code for rec in params]
        return res


class ServiceMethod(Model):
    """Service метод"""

    __tablename__ = 'service_method'

    method_code = Column(db.String(80), unique=True, nullable=False)  # service method/rest method
    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_service_method')

    __table_args__ = (
        UniqueConstraint('entity_id', 'method_code', name='_entity_method_name_uc'),
    )

    @classmethod
    def get_entity(cls, method_code):
        method = cls.query.join(
            Entity, Entity.id == cls.entity_id
        ).join(
            System, System.id == Entity.system_id
        ).filter(
            cls.method_code == method_code,
        ).first()
        if not method:
            raise InternalError('Service method not registered in %s' % cls.__name__)
        res = {
            'entity_code': method.entity.code,
            'system_code': method.entity.system.code,
        }
        return res
