#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.childbirth.xform import \
    ChildbirthTulaXForm
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook

parent_id_name = 'card_id'


@module.route('/api/integration/<int:api_version>/card/<' + parent_id_name + '>/childbirth/',
              methods=['POST', 'PUT', 'DELETE'])
@remote_api_method(hook=hook)
def api_childbirth_change(api_version, **kwargs):
    # main_id = kwargs.get(main_id_name)
    parent_id = kwargs.get(parent_id_name)
    data = None
    delete = request.method == 'DELETE'
    xform = ChildbirthTulaXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
    # main_id = data.get('main_id')
    # xform.check_params(card_id, main_id, data)
    service_name = sys._getframe().f_code.co_name
    parents_params = {
        parent_id_name: {'entity': TulaEntityCode.CARD, 'id': parent_id},
    }
    xform.send_messages(parent_id, parent_id_name, data, service_name, request.method, parents_params)
