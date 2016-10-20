#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
# from cPickle import Pickler
from json import dumps
from collections import OrderedDict

from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.models.entity import Entity, DiffEntityImage
from sirius.models.operation import OperationCode
from sirius.database import db
from zeep.xsd.valueobjects import CompoundValue


class Difference(object):

    def mark_diffs(self, entity_packages):
        # пометить изменения в Хранилище и в пакете
        # в пакете проставляются operation_code, is_changed, удаляемые записи
        flat_entities = {}
        system_code = entity_packages['system_code']
        entities = entity_packages['entities']
        self.build_flat_entities(flat_entities, entities)
        self.set_diffs(system_code, flat_entities)
        self.mark_entities(flat_entities)
        return entity_packages

    def build_flat_entities(self, flat_entities, package_data, level=1):
        for entity_code, records in package_data.iteritems():
            for record in records:
                flat_entities.setdefault((level, entity_code), {}).update(
                    {record['main_id']: record}
                )
                childs = record.get('childs')
                if childs:
                    self.build_flat_entities(flat_entities, childs, level + 1)

    def set_diffs(self, system_code, flat_entities):
        DiffEntityImage.create_temp_table()
        for (level, entity_code), fl_entity_dict in flat_entities.iteritems():
            entity_id = Entity.get_id(system_code, entity_code)
            objects = [
                {
                    'entity_id': entity_id,
                    'root_external_id': (package_record.get('root_parent') or {}).get('main_id', main_id),
                    'external_id': main_id,
                    'content': dumps(self.serialize_object(package_record['data']), cls=WebMisJsonEncoder),
                    'operation_code': OperationCode.READ_ALL,
                    'level': level,
                }
                for main_id, package_record in fl_entity_dict.iteritems()
            ]
            DiffEntityImage.fill_temp_table(objects)
        DiffEntityImage.set_changed_data()
        DiffEntityImage.set_new_data()
        DiffEntityImage.set_deleted_data()

    def mark_entities(self, flat_entities):
        diff_records = DiffEntityImage.get_marked_data()
        for diff_rec in diff_records:
            key = (diff_rec.level, diff_rec.entity.code)
            fl_entity_dict = flat_entities[key]
            if diff_rec.operation_code != OperationCode.DELETE or diff_rec.level == 1:
                # остальные уровни обработаются уже во внешнем приложении
                package_record = fl_entity_dict[diff_rec.external_id]
                root_parent = package_record.get('root_parent')
                if root_parent:
                    root_parent['operation_code'] = OperationCode.CHANGE
                package_record['operation_code'] = diff_rec.operation_code
                (root_parent if root_parent else package_record)['is_changed'] = True

    def save_all_changes(self):
        # вносит изменения в EntityImage, удаляет временные таблицы
        DiffEntityImage.save_new_data()
        DiffEntityImage.save_changed_data()
        DiffEntityImage.save_deleted_data()
        DiffEntityImage.drop_temp_table()

    def commit_all_changes(self):
        # фиксирует изменения в EntityImage
        # todo: убрать (проверить) комиты в DiffEntityImage
        db.session.commit()

    def place(self, data):
        # размещает в хранилище данные
        # todo:
        pass

    @classmethod
    def serialize_object(cls, obj):
        """Serialize zeep objects to native python data structures"""
        # from zeep import helpers. incorrect to process list of strings
        if obj is None:
            return obj

        if isinstance(obj, list):
            return [cls.serialize_object(sub) for sub in obj]

        if not isinstance(obj, CompoundValue):
            return obj

        result = OrderedDict()
        for key in obj:
            value = obj[key]
            if isinstance(value, (list, CompoundValue)):
                value = cls.serialize_object(value)
            result[key] = value
        return result
