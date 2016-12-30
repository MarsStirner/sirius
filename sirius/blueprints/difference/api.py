#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
# from cPickle import Pickler
from json import dumps
from collections import OrderedDict
import xmltodict
import xml.etree.ElementTree as ET

from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.difference.models.image import DiffEntityImage
from sirius.blueprints.monitor.exception import module_entry
from sirius.models.entity import Entity
from sirius.models.operation import OperationCode
from sirius.database import db
from suds.sudsobject import asdict
from zeep.xsd.valueobjects import CompoundValue


class Difference(object):
    """
    Проставляет исходную операцию и признак изменения основной сущности
    """
    # todo: рассмотреть возможность работы модуля после реформатора
    # доп. затраты на обработку ожидаются не большие (по очереди пока не ясно),
    # но появится возможность отсекать сущности, где менялись не используемые
    # поля. если логика реформатора поменялась, то сообщения
    # в очереди остаются валидными. транзакция сохранения
    # сопоставления и диффа остается на одной стороне от брокера
    # (возможно не актуально). возможность перегруппировки сущностей при их
    # сборке, а не на этапе упаковки в пакеты
    # проблемное место рассмотрения - обработка сопутствующих элементов (+/-)

    # todo: добавить выбор сериализатора в json в зависимости от
    # клиента (может из клиента уже сериализованным давать)
    # todo: добавить root_entity_id (stream_id) в EntityImage, DiffEntityImage
    # конфликт TambovEntityCode.BIRTH с TambovEntityCode.SMART_PATIENT
    # одинаковый root_external_id при удалении в разных потоках.
    # нет удаления основной сущности.
    # проверять по root_entity_id, считая, что не будет одинаковых сущностей
    # 1-го уровня в разных потоках, либо по stream_id (надо везде прокидывать)
    # конфликт удаления по разным кускам списков (мероприятия по разным
    # пациентам, врачи по разным ЛПУ) вводить мастер ИД и мастер сущность.
    # проверку дифф включать в билдере. только там, где нужно удаление по списку

    # todo: addition записи в _build_flat_entities схлопываются, когда на них
    # несколько main записей (врач, должность). (из-за этого лишние change).
    # переделать ключ

    is_diff_check = True
    is_delete_check = True
    key_range = None
    json_dumper = None

    # def __init__(self, json_dumper):
    #     self.json_dumper = json_dumper

    @module_entry
    def mark_diffs(self, entity_package):
        """
        пометить изменения в Хранилище и в пакете
        в пакете проставляются operation_code, is_changed, удаляемые записи
        """
        if not entity_package.is_diff_check:
            self.is_diff_check = False
            return entity_package
        self.is_delete_check = entity_package.is_delete_check
        self.key_range = entity_package.get_diff_key_range()

        flat_entities = {}
        system_code = entity_package.system_code
        pack_entities = entity_package.get_pack_entities()

        self._build_flat_entities(flat_entities, pack_entities)
        self._set_diffs(system_code, flat_entities)
        self._mark_entities(entity_package, flat_entities)
        db.session.commit()
        return entity_package

    def _build_flat_entities(self, flat_entities, pack_entities, level=1):
        for entity_code, records in pack_entities.iteritems():
            for record in records:
                flat_entities.setdefault((level, entity_code), {}).update(
                    {str(record['main_id']): record}
                )
                additions = record.get('addition')
                if additions:
                    self._build_flat_entities(flat_entities, additions, level + 1)
                childs = record.get('childs')
                if childs:
                    self._build_flat_entities(flat_entities, childs, level + 1)

    def _set_diffs(self, system_code, flat_entities):
        # DiffEntityImage.create_temp_table()
        DiffEntityImage.clear_temp_table()
        root_ext_ids = set()
        for (level, entity_code), fl_entity_dict in flat_entities.iteritems():
            entity_id = Entity.get_id(system_code, entity_code)
            objects = (
                {
                    'entity_id': entity_id,
                    'root_external_id': (package_record.get('root_parent') or {}).get('main_id', main_id),
                    'external_id': main_id,
                    'key': package_record.get('diff_key'),
                    'content': self._dump_content(package_record['data']),
                    'operation_code': OperationCode.READ_MANY,
                    'level': level,
                }
                for main_id, package_record in fl_entity_dict.iteritems()
            )
            ids = DiffEntityImage.fill_temp_table(objects)
            root_ext_ids.update(ids)
        if self.is_delete_check:
            # после того как все записи добавлены можно смотреть чего не хватает
            for root_ext_id in root_ext_ids:
                DiffEntityImage.set_deleted_data(root_ext_id, self.key_range)
        DiffEntityImage.set_changed_data(self.key_range)
        DiffEntityImage.set_new_data(self.key_range)

    def _mark_entities(self, entity_package, flat_entities):
        diff_records = DiffEntityImage.get_marked_data()
        for diff_rec in diff_records:
            if diff_rec.operation_code != OperationCode.DELETE:
                key = (diff_rec.level, diff_rec.entity.code)
                fl_entity_dict = flat_entities[key]
                package_record = fl_entity_dict[diff_rec.external_id]
                root_parent = package_record.get('root_parent')
                if root_parent:
                    root_parent['operation_code'] = OperationCode.CHANGE
                package_record['operation_code'] = diff_rec.operation_code
                (root_parent if root_parent else package_record)['is_changed'] = True
            else:
                # остальные уровни обработаются уже во внешнем приложении
                if diff_rec.level == 1:
                    entity_package.add_main_pack_entity(
                        entity_code=diff_rec.entity.code,
                        method=None,
                        main_param_name=None,
                        main_id=diff_rec.external_id,
                        parents_params=None,
                        data=None,
                        operation_code=diff_rec.operation_code,
                        is_changed=True,
                    )
                else:
                    key = (diff_rec.level, diff_rec.entity.code)
                    fl_entity_dict = flat_entities[key]
                    package_record = fl_entity_dict[diff_rec.external_id]
                    root_parent = package_record.get('root_parent')
                    root_parent['operation_code'] = OperationCode.CHANGE

    # def save_all_changes(self):
    #     # вносит изменения в EntityImage, удаляет временные таблицы
    #     DiffEntityImage.save_new_data()
    #     DiffEntityImage.save_changed_data()
    #     DiffEntityImage.save_deleted_data()
    #     DiffEntityImage.drop_temp_table()

    @module_entry
    def save_change(self, msg):
        """
        вносит изменения в EntityImage
        """
        if not self.is_diff_check:
            return
        meta = msg.get_header().meta
        main_id = meta['remote_main_id']
        operation_code = meta['remote_operation_code']
        if operation_code == OperationCode.ADD:
            DiffEntityImage.save_new_data(main_id)
        elif operation_code == OperationCode.CHANGE:
            DiffEntityImage.save_changed_data(main_id)
        else:
            assert operation_code == OperationCode.DELETE
            DiffEntityImage.save_deleted_data(main_id)
        db.session.commit()

    def commit_all_changes(self):
        """
        удаляет временные таблицы
        """
        if not self.is_diff_check:
            return
        # DiffEntityImage.drop_temp_table()
        DiffEntityImage.clear_temp_table()
        # фиксирует изменения в EntityImage, EntityImageDiff
        # todo: убрать комиты в conformity_local.. (разные сессии по сторонам селери)
        # todo: комит по каждой записи отдельно - save_change. совместно с conformity_local, (conformity_remote?)
        db.session.commit()

    def place(self, data):
        # размещает в хранилище данные
        # todo:
        pass

    def _dump_content(self, data):
        if isinstance(data, ''):
            res = dumps(self.serialize_object(data), cls=WebMisJsonEncoder)  # zeep
        elif type(data) == 'instance':
            res = dumps(self.recursive_asdict(data), cls=WebMisJsonEncoder)  # suds
        elif isinstance(data, dict):
            res = self.json_dumper(data)  # json
        elif isinstance(data, basestring):  # если убрать сериализаторы в transfer, то неоднозначности не будет
            res = dumps(xmltodict.parse(ET.tostring(data, encoding='utf-8', method='xml')), encoding=WebMisJsonEncoder)  # ET
        else:
            res = unicode(data)
        return res

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

    @classmethod
    def recursive_asdict(cls, d):
        """Convert Suds object into serializable format."""
        out = {}
        for k, v in asdict(d).iteritems():
            if hasattr(v, '__keylist__'):
                out[k] = cls.recursive_asdict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(cls.recursive_asdict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out
