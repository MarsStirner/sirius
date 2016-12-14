#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.specialists_checkup.xform import \
    SpecialistsCheckupTulaXForm
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook

main_id_name = 'result_action_id'
parent_id_name = 'card_id'


@module.route('/api/integration/<int:api_version>/card/<' + parent_id_name + '>/measures/specialists_checkup',
              methods=['POST'])
@module.route('/api/integration/<int:api_version>/card/<' + parent_id_name + '>/measures/specialists_checkup/<' + main_id_name + '>',
              methods=['PUT', 'DELETE'])
@remote_api_method(hook=hook)
def api_specialists_checkup_change(api_version, **kwargs):
    main_id = kwargs.get(main_id_name)
    parent_id = kwargs.get(parent_id_name)
    data = None
    delete = request.method == 'DELETE'
    xform = SpecialistsCheckupTulaXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
        main_id = main_id or data.get(main_id_name)
    # xform.check_params(card_id, main_id, data)
    service_name = sys._getframe().f_code.co_name
    parents_params = {
        parent_id_name: {'entity': TulaEntityCode.CARD, 'id': parent_id},
    }
    xform.send_messages(main_id, main_id_name, data, service_name, request.method, parents_params)
