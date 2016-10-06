#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.remote_service.tula.app import module
from sirius.blueprints.remote_service.lib.producer import RemoteProducer
from sirius.blueprints.remote_service.tula.lib.reformer import RemoteEntity
from sirius.blueprints.remote_service.tula.views import remote_system_code
from sirius.blueprints.remote_service.tula.views.client.schemas import \
    ClientSchema
from sirius.blueprints.remote_service.lib.xform import XForm
from sirius.lib.apiutils import api_method
from sirius.lib.message import Message


client_id_name = 'client_id'


@module.route('/api/integration/<int:api_version>/client/<int:' + client_id_name + '>',
              methods=['PUT', 'POST', 'DELETE'])
@api_method
def api_client_change(api_version, **kwargs):
    client_id = kwargs.get(client_id_name)
    data = None
    delete = request.method == 'DELETE'
    xform = ClientXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
    # client_id = data.get('client_id')
    # xform.check_params(card_id, client_id, data)
    method_name = sys._getframe().f_code.co_name
    xform.send_messages(RemoteEntity.CLIENT, client_id, client_id_name, data, method_name, request.method)


class ClientXForm(ClientSchema, XForm):

    def send_messages(self, entity_code, entity_id, param_name, data, method_name, method_code):
        msg = Message(data)
        msg.to_local_service()
        msg.set_send_data_type()
        msg.get_header().meta.update({
            'remote_system_code': remote_system_code,
            'remote_entity_code': entity_code,
            'remote_service_code': method_name,
            'remote_main_id': entity_id,
            'remote_main_param_name': param_name,
            'remote_method': method_code,
        })

        # todo: цикл вложенных дозапросов и связывание ответов
        # from sirius.lib.implement import Implementation
        # implement = Implementation()
        # reformer = implement.get_reformer(remote_system_code)
        # miss_reqs = reformer.get_missing_requests(msg)
        # miss_data = reformer.transfer_give_data(miss_reqs)
        # msg.add_missing_data(miss_data)

        # data_store = DataStore()

        producer = RemoteProducer()
        producer.send(msg)
