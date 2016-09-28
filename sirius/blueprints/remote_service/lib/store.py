#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""


class DataStore(object):
    diff_data = None

    def build_diffs(self, data):
        # todo:
        self.set_all_data_table(data)
        self.diff_data = {
            'added': self.set_new_data_table(),
            'changed': self.set_changed_data_table(),
            'deleted': self.set_deleted_data_table(),
        }

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
