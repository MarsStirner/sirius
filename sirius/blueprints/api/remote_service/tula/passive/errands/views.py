#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from flask import request
from hitsl_utils.api import api_method
from sirius.blueprints.api.remote_service.tula.app import module

# todo:


@module.route('/api/integration/tula/<int:api_version>/card/errands/', methods=['GET'])
@api_method
def api_integr_errands_get(api_version):
    xform = ErrandListXForm(api_version)
    return xform.get_data('errands')


class ErrandListXForm(object):
    def get_data(self, entity_code):
        data_store = Difference()
        return data_store.get_entity_data(entity_code)
