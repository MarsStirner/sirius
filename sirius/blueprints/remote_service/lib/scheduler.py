#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.remote_service.lib.implement import Implementation
from sirius.blueprints.remote_service.lib.producer import RemoteProducer
from sirius.blueprints.remote_service.lib.store import DataStore
from sirius.lib.message import Message
from sirius.lib.remote_system import remote_system


class Scheduler(object):
    def execute(self):
        rmt_sys_code = remote_system.get_master_system_code()
        implement = Implementation()
        reformer = implement.get_reformer(rmt_sys_code)
        data_store = DataStore()
        for ent in self.get_entities_list():
            msg = self.create_entity_data_request_msg(ent)
            remote_reformed_data = reformer.to_remote(msg)
            entity_data = transfer.execute(remote_reformed_data)
            self.send_diff_data(entity_data, data_store, reformer)

    def send_diff_data(self, entity_data, data_store, reformer):
        producer = RemoteProducer()
        data_store.build_diffs(entity_data)
        data_store.save_all_changes()
        post_msgs = reformer.create_local_post_msgs(data_store.get_added())
        put_msgs = reformer.create_local_put_msgs(data_store.get_changed())
        del_msgs = reformer.create_local_del_msgs(data_store.get_deleted())
        for next_msg in (post_msgs + put_msgs + del_msgs):
            producer.send(next_msg, async=False)
        data_store.commit_all_changes()

    def create_entity_data_request_msg(self, entity):
        # создает сообщение с параметрами, по которым сообщение реформируется
        # в данные для правильного запроса сущностей из Удаленной системы
        # todo:
        msg = Message()
        return msg

    def get_entities_list(self):
        # список кодов сущностей, которые нужно запрашивать как мастер-данные
        # из пассивной системы
        # todo:
        return []
