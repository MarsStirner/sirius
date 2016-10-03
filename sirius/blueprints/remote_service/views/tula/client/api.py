#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from hitsl_utils.api import api_method
from sirius.blueprints.remote_service.app import module
from sirius.blueprints.remote_service.lib.producer import RemoteProducer
from sirius.blueprints.remote_service.lib.tula.reformer import TulaReformer, \
    RemoteEntity
from sirius.blueprints.remote_service.views.tula.client.schemas import \
    ClientSchema
from sirius.blueprints.remote_service.views.xform import XForm
from sirius.lib.message import Message


@module.route('/api/integration/<int:api_version>/client/<int:client_id>', methods=['PUT', 'POST', 'DELETE'])
@api_method
def api_client_change(api_version, client_id=None):
    data = None
    delete = request.method == 'DELETE'
    xform = ClientXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
    # client_id = data.get('client_id')
    # xform.check_params(card_id, client_id, data)
    method_name = sys._getframe().f_code.co_name
    xform.send_messages(RemoteEntity.CLIENT, client_id, data, method_name, request.method)


class ClientXForm(ClientSchema, XForm):

    def send_messages(self, entity_code, entity_id, data, method_name, method_code):
        producer = RemoteProducer()
        reformer = TulaReformer()
        # data_store = DataStore()
        # msgs = reformer.create_local_msgs(data, method_code)
        operation_code = reformer.get_operation_code_by_method(method_code)
        msg = Message(data)
        msg.to_local_service()
        msg.set_send_data_type()
        msg.get_header().meta.update({
            'remote_system_code': 'TULA',  # todo
            'remote_entity_code': entity_code,
            'remote_service_code': method_name,
            'remote_main_id': entity_id,
            'remote_operation_code': operation_code,
        })
        msgs = reformer.reform_msg(msg)
        for next_msg in msgs:
            producer.send(next_msg)
