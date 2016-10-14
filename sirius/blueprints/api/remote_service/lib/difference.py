#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
# from cPickle import Pickler

from sirius.models.entity import EntityImage


class Difference(object):
    diff_data = None

    def build_diffs(self, data):
        # todo:
        EntityImage.set_all_data_table(data)
        self.diff_data = {
            'added': self.set_new_data_table(),
            'changed': self.set_changed_data_table(),
            'deleted': self.set_deleted_data_table(),
        }

    def check_diffs(self, package_data):
        # пометить изменения в Хранилище и в пакете
        # в пакете нужно проставить src_operation_code
        self.set_all_data_table(package_data)

    def save_all_changes(self):
        # вносит изменения в таблицу сообщений данных, удаляет временные таблицы
        # todo:
        data = []
        self.place(data)

    def commit_all_changes(self):
        # фиксирует изменения в таблице сообщений
        # todo:
        pass

    def get_added(self):
        return self.diff_data.get('added')

    def get_changed(self):
        return self.diff_data.get('changed')

    def get_deleted(self):
        return self.diff_data.get('deleted')

    def place(self, data):
        # размещает в хранилище данные
        # todo:
        pass
