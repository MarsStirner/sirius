#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.passive.client.xform import \
    ClientTulaXForm
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook

client_id_name = 'client_id'


@module.route('/api/integration/<int:api_version>/client/', methods=['POST'])
@module.route('/api/integration/<int:api_version>/client/<' + client_id_name + '>',
              methods=['PUT', 'DELETE'])
@remote_api_method(hook=hook)
def api_client_change(api_version, **kwargs):
    client_id = kwargs.get(client_id_name)
    stream_id = kwargs.get('stream_id')
    data = None
    delete = request.method == 'DELETE'
    xform = ClientTulaXForm(api_version, stream_id)
    if not delete:
        data = request.get_json()
        xform.validate(data)
        client_id = client_id or data.get(client_id_name)
    # xform.check_params(card_id, client_id, data)
    service_name = sys._getframe().f_code.co_name
    xform.send_messages(client_id, client_id_name, data, service_name, request.method)
