#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from flask import request
from sirius.blueprints.api.remote_service.tula.app import module

# todo:
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook


@module.route('/api/integration/tula/<int:api_version>/card/errands/', methods=['GET'])
@remote_api_method(hook=hook)
def api_integr_errands_get(api_version):
    xform = ErrandListXForm(api_version)
    return xform.get_data('errands')


class ErrandListXForm(object):
    def get_data(self, entity_code):
        data_store = Difference()
        return data_store.get_entity_data(entity_code)
