#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.passive.org_department.xform import \
    OrgDepartmentTulaXForm
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook

main_id_name = 'regionalCode'


@module.route('/api/integration/<int:api_version>/organization_department/',
              methods=['POST'])
@module.route('/api/integration/<int:api_version>/organization_department/<' + main_id_name + '>',
              methods=['PUT', 'DELETE'])
@remote_api_method(hook=hook)
def api_org_department_change(api_version, **kwargs):
    main_id = kwargs.get(main_id_name)
    stream_id = kwargs.get('stream_id')
    data = None
    delete = request.method == 'DELETE'
    xform = OrgDepartmentTulaXForm(api_version, stream_id)
    if not delete:
        data = request.get_json()
        xform.validate(data)
        main_id = main_id or data.get(main_id_name)
    # xform.check_params(card_id, main_id, data)
    service_name = sys._getframe().f_code.co_name
    xform.send_messages(main_id, main_id_name, data, service_name, request.method)
