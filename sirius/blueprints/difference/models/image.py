#! coding:utf-8
"""


@author: BARS Group
@date: 28.09.2016

"""
from sqlalchemy import UniqueConstraint, CheckConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sirius.database import Column, Model, db, reference_col, relationship
from sirius.models.entity import Entity
from sirius.models.operation import OperationCode


class EntityImage(Model):
    """Отпечаток содержимого сущностей удаленных систем"""

    __tablename__ = 'entity_image'

    root_entity_id = reference_col('entity', unique=False, nullable=False)
    root_entity = relationship('Entity', backref='set_entity_image_by_root',
                               foreign_keys='EntityImage.root_entity_id')
    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_entity_image',
                          foreign_keys='EntityImage.entity_id')
    parent_id = reference_col('entity_image', unique=False, nullable=True)
    parent = relationship('EntityImage')
    root_external_id = Column(db.String(80), unique=False, nullable=False)
    external_id = Column(db.String(80), unique=False, nullable=False, index=True)
    key = Column(db.String(80), unique=False, nullable=False, index=True, server_default='')
    content = Column(JSONB, unique=False, nullable=False)
    level = Column(db.Integer, unique=False, nullable=False)
    created = Column(db.DateTime, unique=False, nullable=False, server_default=text('now()'))
    modified = Column(db.DateTime, unique=False, nullable=False,
                      server_default=text('now()'), server_onupdate=text('now()'))


class EntityImageDiff(Model):
    __tablename__ = 'entity_image_diff'

    root_entity_id = reference_col('entity', unique=False, nullable=False)
    root_entity = relationship('Entity', backref='set_entity_image_diff_by_root',
                               foreign_keys='EntityImageDiff.root_entity_id')
    entity_id = reference_col('entity', unique=False, nullable=False)
    entity = relationship('Entity', backref='set_entity_image_diff',
                          foreign_keys='EntityImageDiff.entity_id')
    root_external_id = Column(db.String(80), unique=False, nullable=False)
    external_id = Column(db.String(80), unique=False, nullable=False, index=True)
    key = Column(db.String(80), unique=False, nullable=False, index=True, server_default='')
    content = Column(JSONB, unique=False, nullable=True)
    operation_code = Column(db.String(80), unique=False, nullable=False)
    level = Column(db.Integer, unique=False, nullable=False)

    __table_args__ = {'prefixes': ['TEMPORARY']}


class DiffEntityImage(object):  # todo: перенести методы в EntityImageDiff
    temp_table_name = EntityImageDiff.__tablename__

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
                    ('root_entity_id', 'integer NOT NULL'),
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
    def clear_temp_table(cls):
        drop_query = '''
        DELETE FROM %(table_name)s;
        ''' % ({'table_name': cls.temp_table_name})
        db.session.execute(drop_query)

    @classmethod
    def set_new_data(cls, key_range):
        # tmp.content != 'null'
        # пропускаем старые записи, добавленные для определения удаленных
        # возможно стоит указывать такие явно в ключе. старые пока только в пациентах

        key_range_beg = key_range_end = ''
        if key_range:
            key_range_beg = key_range[0]
            key_range_end = key_range[1]

        set_query = '''
        update %(temp_table_name)s t
        set operation_code = '%(operation_code)s'
        from (
          select tmp.id
          from %(temp_table_name)s tmp
          where
            tmp.content != 'null' and
            not exists(
              select store.id
                from %(store_table_name)s store
                where
                  store.root_entity_id = tmp.root_entity_id and
                  store.root_external_id = tmp.root_external_id and
                  store.entity_id = tmp.entity_id and
                  store.external_id = tmp.external_id and
                  (
                    '%(key_range_beg)s' = '' or
                    store.key between '%(key_range_beg)s' and '%(key_range_end)s'
                  )
            )
        ) sq
        where
          t.id = sq.id;
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.ADD,
            'key_range_beg': key_range_beg,
            'key_range_end': key_range_end,
        })
        db.session.execute(set_query)

    @classmethod
    def set_changed_data(cls, key_range):
        # tmp.content != 'null'
        # пропускаем старые записи, добавленные для определения удаленных
        # возможно стоит указывать такие явно в ключе. старые пока только в пациентах

        key_range_beg = key_range_end = ''
        if key_range:
            key_range_beg = key_range[0]
            key_range_end = key_range[1]

        set_query = '''
        update %(temp_table_name)s t
        set operation_code = '%(operation_code)s'
        from (
          select tmp.id
          from %(temp_table_name)s tmp
          join %(store_table_name)s store on
            store.root_entity_id = tmp.root_entity_id and
            store.root_external_id = tmp.root_external_id and
            store.entity_id = tmp.entity_id and
            store.external_id = tmp.external_id
          where
            tmp.content != 'null' and
            store.content != tmp.content and
            (
              '%(key_range_beg)s' = '' or
              store.key between '%(key_range_beg)s' and '%(key_range_end)s'
            )
        ) sq
        where
          t.id = sq.id;
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.CHANGE,
            'key_range_beg': key_range_beg,
            'key_range_end': key_range_end,
        })
        db.session.execute(set_query)

    @classmethod
    def set_deleted_data(cls, root_entity_id, key_range):
        key_range_beg = key_range_end = ''
        if key_range:
            key_range_beg = key_range[0]
            key_range_end = key_range[1]

        # content, -- убрать, если не понадобится
        set_query = '''
        insert into %(temp_table_name)s
        (
          root_entity_id,
          entity_id,
          root_external_id,
          external_id,
          key,
          -- content,
          operation_code,
          level
        )
        (
          select
            store.root_entity_id,
            store.entity_id,
            store.root_external_id,
            store.external_id,
            store.key,
            -- store.content,
            '%(operation_code)s',
            store.level
          from %(store_table_name)s store
          where
            store.root_entity_id = '%(root_entity_id)s' and
            (
              '%(key_range_beg)s' = '' or
              store.key between '%(key_range_beg)s' and '%(key_range_end)s'
            ) and
            not exists(
              select tmp.id
                from %(temp_table_name)s tmp
                where
                  store.root_entity_id = tmp.root_entity_id and  -- не обяз. но страховка
                  store.root_external_id = tmp.root_external_id and
                  store.entity_id = tmp.entity_id and
                  store.external_id = tmp.external_id
            )
        );
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.DELETE,
            'root_entity_id': root_entity_id,
            'key_range_beg': key_range_beg,
            'key_range_end': key_range_end,
        })
        db.session.execute(set_query)

    @classmethod
    def save_new_data(cls, root_external_id):
        set_query = '''
        insert into %(store_table_name)s
        (
          entity_id,
          root_external_id,
          external_id,
          content,
          level,
          key
        )
        (
          select
            tmp.entity_id,
            tmp.root_external_id,
            tmp.external_id,
            tmp.content,
            tmp.level,
            tmp.key
          from %(temp_table_name)s tmp
          where
            tmp.operation_code = '%(operation_code)s'
            and tmp.root_external_id = '%(root_external_id)s'
        );
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.ADD,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def save_changed_data(cls, root_external_id):
        set_query = '''
        update %(store_table_name)s store
        set content = sq.content
        from (
          select tmp.content, tmp.entity_id, tmp.external_id
          from %(temp_table_name)s tmp
          where
            tmp.operation_code = '%(operation_code)s'
            and tmp.root_external_id = '%(root_external_id)s'
        ) sq
        where
          store.entity_id = sq.entity_id and
          store.external_id = sq.external_id;
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.CHANGE,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def save_deleted_data(cls, root_external_id):
        set_query = '''
        delete from %(store_table_name)s store
        using %(temp_table_name)s tmp
        where
          tmp.operation_code = '%(operation_code)s' and
          tmp.root_external_id = '%(root_external_id)s' and
          store.entity_id = tmp.entity_id and
          store.external_id = tmp.external_id;
        ''' % ({
            'temp_table_name': cls.temp_table_name,
            'store_table_name': EntityImage.__tablename__,
            'operation_code': OperationCode.DELETE,
            'root_external_id': root_external_id,
        })
        db.session.execute(set_query)

    @classmethod
    def get_marked_data(cls):
        # set_query = '''
        # select tmp.*
        # from %(temp_table_name)s tmp
        # where
        #   tmp.operation_code != %(operation_code)s
        # order by tmp.level desc;
        # ''' % ({
        #     'temp_table_name': cls.temp_table_name,
        #     'operation_code': OperationCode.READ_MANY,
        # })
        # db.session.execute(set_query)
        return EntityImageDiff.query.join(
            Entity, Entity.id == EntityImageDiff.entity_id
        ).filter(
            EntityImageDiff.operation_code != OperationCode.READ_MANY,
        ).order_by(EntityImageDiff.level.desc()).all()
