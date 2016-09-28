#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.lib.message import Message


class Reformer(object):
    orig_msg = None
    # direct = None

    def to_remote(self, msg):
        # todo:
        self.orig_msg = msg
        # self.direct = 'remote'
        # res = self.reform_msg()
        return res

    def to_local(self, msg):
        # todo:
        self.orig_msg = msg
        # self.direct = 'local'
        # res = self.reform_msg()
        return res

    def reform_msg(self):
        pass

    def local_conformity(self, remote_data, local_data):
        # сопоставление ID в БД при добавлении данных
        # todo:
        pass

    def remote_conformity(self, local_data, remote_data):
        # сопоставление ID в БД при добавлении данных
        # todo:
        pass

    def create_local_msgs(self, data, method):
        if method.upper == 'POST':
            res = self.create_local_post_msgs({'added': data})
        elif method.upper == 'PUT':
            res = self.create_local_put_msgs({'changed': data})
        elif method.upper == 'DELETE':
            res = self.create_local_del_msgs({'deleted': data})
        else:
            raise Exception('Unexpected method')
        return res

    def create_local_post_msgs(self, diff_data):
        # создание списка сообщений для добавления в локальную систему
        # сущностей, описанных в diff_data
        # todo:
        for remote_data in diff_data.get('added'):
            local_data = self.to_local(remote_data)
            msg = Message(local_data)
            msg.set_source_data(remote_data)
        return []

    def create_local_put_msgs(self, diff_data):
        # создание списка сообщений для изменения в локальную систему
        # сущностей, описанных в diff_data
        diff_data.get('changed')
        # todo:
        return []

    def create_local_del_msgs(self, diff_data):
        # создание списка сообщений для удаления в локальную систему
        # сущностей, описанных в diff_data
        diff_data.get('deleted')
        # todo:
        return []
