#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.passive.client.xform import \
    TulaClientXForm
from sirius.lib.apiutils import api_method

client_id_name = 'client_id'


@module.route('/api/integration/<int:api_version>/client/<int:' + client_id_name + '>',
              methods=['PUT', 'POST', 'DELETE'])
@api_method(authorization=False)
def api_client_change(api_version, **kwargs):
    client_id = kwargs.get(client_id_name)
    data = None
    delete = request.method == 'DELETE'
    xform = TulaClientXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
    # client_id = data.get('client_id')
    # xform.check_params(card_id, client_id, data)
    service_name = sys._getframe().f_code.co_name
    xform.send_messages(client_id, client_id_name, data, service_name, request.method)
