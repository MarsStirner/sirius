#! coding:utf-8
"""


@author: BARS Group
@date: 10.10.2016

"""
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.models.operation import OperationCode
from sirius.models.system import System
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB


class Entity(Model):
    """Сущности удаленной и локальной систем"""

    __tablename__ = 'entity'

    code = Column(db.String(80), unique=False, nullable=False)
    system_id = reference_col('system', unique=False, nullable=False)
    system = relationship('System', backref='set_entity')

    __table_args__ = (
        UniqueConstraint('system_id', 'code', name='_sys_entity_uc'),
    )

    @classmethod
    def get_id(cls, system_code, entity_code):
        entity_id = cls.query.join(
            System, System.id == cls.system_id
        ).filter(
            cls.code == entity_code,
            System.code == system_code,
        ).value(cls.id)
        return entity_id


class EntityImage(Model):
    """Отпечаток содержимого сущностей удаленных систем"""

    __tablename__ = 'entity_image'

    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_entity_image')
    parent_id = reference_col('entity_image', unique=False, nullable=True)
    parent = relationship('EntityImage')
    root_external_id = Column(db.String(80), unique=False, nullable=False)
    external_id = Column(db.String(80), unique=False, nullable=False, index=True)
    content = Column(JSONB, unique=False, nullable=False)


class _DiffEntityImage(Model):
    __tablename__ = 'temp_entity_image'

    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_diff_entity_image')
    root_external_id = Column(db.String(80), unique=False, nullable=False)
    external_id = Column(db.String(80), unique=False, nullable=False, index=True)
    content = Column(JSONB, unique=False, nullable=True)
    operation_code = Column(db.String(80), unique=False, nullable=False)
    level = Column(db.Integer, unique=False, nullable=False)

    __table_args__ = {'prefixes': ['TEMPORARY']}


class DiffEntityImage(object):
    temp_table_name = 'temp_entity_image'

    @classmethod
    def create_temp_table(cls):
        create_query = '''
        CREATE TEMP TABLE IF NOT EXISTS %(table_name)s (%(columns)s);
        CREATE INDEX IF NOT EXISTS %(table_name)s_entity_id
          ON %(table_name)s
          USING btree
          (entity_id);
        CREATE INDEX IF NOT EXISTS %(table_name)s_external_id
          ON %(table_name)s
          USING btree
          (external_id);
        DELETE FROM %(table_name)s;
        ''' % ({
            'table_name': cls.temp_table_name,
            'columns': ', '.join((
                x[0].join(['"', '"']) + ' ' + x[1] for x in (
                    ('id', 'serial NOT NULL'),
                    ('entity_id', 'integer NOT NULL'),
                    ('root_external_id', 'character varying(80) NOT NULL'),
                    ('external_id', 'character varying(80) NOT NULL'),
                    ('content', 'jsonb'),
                    ('operation_code', 'character varying(80) NOT NULL'),
                    ('level', 'integer NOT NULL'),
                )
            )),
        })
        db.session.execute(create_query)

    @classmethod
    def fill_temp_table(cls, data):
        insert_query = '''
        INSERT INTO %(table_name)s (%(columns)s) VALUES (%(values)s)
        '''
        for r in data:
            keys, vals = zip(*r.items())
            db.session.execute(
                insert_query % ({
                    'table_name': cls.temp_table_name,
                    'columns': ', '.join(keys),
                    'values': ', '.join((
                        unicode(x is not None and x or '').join(("'", "'"))
                        for x in vals
                    )),
                }))

    @classmethod
    def drop_temp_table(cls):
        drop_query = '''
        DROP TABLE IF EXISTS %(table_name)s;
        ''' % ({'table_name': cls.temp_table_name})
        db.session.execute(drop_query)

    @classmethod
    def set_new_data(cls):
        # src.content != 'null'
        # пропускаем старые записи, добавленные для определения удаленных
        # возможно стоит указывать такие явно в ключе. старые пока только в пациентах

        set_query = '''
        update %(src_table_name)s t
        set operation_code = '%(operation_code)s'
        from (
          select src.id
          from %(src_table_name)s src
          where
            src.content != 'null' and
            not exists(
              select chk.id
                from %(chk_table_name)s chk
                where
                  chk.entity_id = src.entity_id and
                  chk.external_id = src.external_id
            )
        ) sq
        where
          t.id = sq.id;
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.ADD,
        })
        db.session.execute(set_query)

    @classmethod
    def set_changed_data(cls):
        # src.content != 'null'
        # пропускаем старые записи, добавленные для определения удаленных
        # возможно стоит указывать такие явно в ключе. старые пока только в пациентах

        set_query = '''
        update %(src_table_name)s t
        set operation_code = '%(operation_code)s'
        from (
          select src.id
          from %(src_table_name)s src
          join %(chk_table_name)s chk on
            chk.entity_id = src.entity_id and
            chk.external_id = src.external_id
          where
            src.content != 'null' and
            chk.content != src.content
        ) sq
        where
          t.id = sq.id;
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.CHANGE,
        })
        db.session.execute(set_query)

    @classmethod
    def set_deleted_data(cls):
        # content, -- убрать, если не понадобится
        set_query = '''
        insert into %(src_table_name)s
        (
          entity_id,
          root_external_id,
          external_id,
          content,
          operation_code
        )
        (
          select
            chk.entity_id,
            chk.root_external_id,
            chk.external_id,
            chk.content,
            '%(operation_code)s'
          from %(chk_table_name)s chk
          where
            not exists(
              select src.id
                from %(src_table_name)s src
                where
                  chk.entity_id = src.entity_id and
                  chk.external_id = src.external_id
            )
        );
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.DELETE,
        })
        db.session.execute(set_query)

    @classmethod
    def save_new_data(cls, root_external_id):
        set_query = '''
        insert into %(chk_table_name)s
        (
          entity_id,
          root_external_id,
          external_id,
          content
        )
        (
          select
            src.entity_id,
            src.root_external_id,
            src.external_id,
            src.content
          from %(src_table_name)s src
          where
            src.operation_code = '%(operation_code)s'
            and src.root_external_id = '%(root_external_id)s'
        );
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.ADD,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def save_changed_data(cls, root_external_id):
        set_query = '''
        update %(chk_table_name)s chk
        set content = sq.content
        from (
          select src.content, src.entity_id, src.external_id
          from %(src_table_name)s src
          where
            src.operation_code = '%(operation_code)s'
            and src.root_external_id = '%(root_external_id)s'
        ) sq
        where
          chk.entity_id = sq.entity_id and
          chk.external_id = sq.external_id;
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.CHANGE,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def save_deleted_data(cls, root_external_id):
        set_query = '''
        delete from %(chk_table_name)s chk
        using %(src_table_name)s src
        where
          src.operation_code = '%(operation_code)s' and
          src.root_external_id = '%(root_external_id)s' and
          chk.entity_id = src.entity_id and
          chk.external_id = src.external_id;
        ''' % ({
            'src_table_name': cls.temp_table_name,
            'chk_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.DELETE,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def get_marked_data(cls):
        # set_query = '''
        # select src.*
        # from %(src_table_name)s src
        # where
        #   src.operation_code != %(operation_code)s
        # order by src.level desc;
        # ''' % ({
        #     'src_table_name': cls.temp_table_name,
        #     'operation_code': OperationCode.READ_ALL,
        # })
        # db.session.execute(set_query)
        return _DiffEntityImage.query.join(
            Entity, Entity.id == _DiffEntityImage.entity_id
        ).filter(
            _DiffEntityImage.operation_code != OperationCode.READ_ALL,
        ).order_by(_DiffEntityImage.level.desc()).all()
