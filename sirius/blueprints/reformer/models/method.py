#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship, \
    XMLType
from sirius.models.entity import Entity
from sirius.models.operation import Operation
from sirius.models.protocol import Protocol, ProtocolCode
from sirius.models.system import System
from sqlalchemy import UniqueConstraint, CheckConstraint


class ApiMethod(Model):
    """API метод"""

    __tablename__ = 'api_method'

    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_api_method')
    operation_id = reference_col('operation', unique=False, nullable=False)
    operation = relationship('Operation', backref='set_api_method')
    protocol_id = reference_col('protocol', unique=False, nullable=False)
    protocol = relationship('Protocol', backref='set_api_method')
    method = Column(db.String(80), unique=False, nullable=False)  # service method/rest method
    template_url = Column(db.Text(), unique=False, nullable=False)  # wsdl uri/rest url template

    __table_args__ = (
        UniqueConstraint('entity_id', 'operation_id', name='_entity_operation_uc'),
        CheckConstraint("protocol_code = '%s' OR wsdl_uri > ''" % ProtocolCode.REST, name='_wsdl_uri_chk'),
    )

    @classmethod
    def get_method(cls, entity_code, operation_code, system_code):
        method = cls.query.join(
            Entity, Entity.id == cls.entity_id
        ).join(
            System, System.id == Entity.system_id
        ).join(
            Operation, Operation.id == cls.operation_id
        ).join(
            Protocol, Protocol.id == cls.protocol_id
        ).filter(
            Entity.code == entity_code,
            Operation.code == operation_code,
            System.code == system_code,
        ).first()
        if not method:
            raise RuntimeError('Service not registered in %s' % cls.__name__)
        sys_url = method.entity.system.url.rstrip('/')
        res = {
            'protocol': method.protocol.code,
            'method': method.method,
            'template_url': sys_url + method.template_url,
        }
        return res
