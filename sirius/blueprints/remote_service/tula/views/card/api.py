#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from sirius.lib.message import Message
from flask import request
from hitsl_utils.api import api_method
from sirius.blueprints.remote_service.app import module

# todo:

@module.route('/api/integration/tula/<int:api_version>/card/', methods=['POST'])
@module.route('/api/integration/tula/<int:api_version>/card/<int:card_id>', methods=['PUT'])
@api_method
def api_card_save(api_version, card_id=None):
    data = request.get_json()
    create = request.method == 'POST'
    xform = CardXForm(api_version, create)
    xform.validate(data)
    # client_id = data.get('client_id')
    # xform.check_params(card_id, client_id, data)
    xform.send_target_obj('card', card_id, data, request.method)


class CardXForm(object):

    def validate(self, data):
        pass

    def send_target_obj(self, entity_code, entity_id, data, method):
        msg = Message(data)
        msg.to_local_service()
        msg.set_send_data_type()

        data_store = DataStore()
        producer = RemoteProducer()
        reformer = TulaReformer()
        msgs = reformer.create_local_msgs(data, method)
        for next_msg in msgs:
            producer.send(next_msg)
