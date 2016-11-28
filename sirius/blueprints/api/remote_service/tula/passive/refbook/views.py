#! coding:utf-8
"""


@author: BARS Group
@date: 03.10.2016

"""
import sys

from flask import request
from sirius.blueprints.api.remote_service.tula.app import module
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.refbook.xform import \
    RefbookTulaXForm
from sirius.blueprints.monitor.exception import remote_api_method
from sirius.blueprints.monitor.logformat import hook

item_code_name = 'code'


@module.route('/api/integration/<int:api_version>/reference_books/<reference_book_code>', methods=['POST'])
@module.route('/api/integration/<int:api_version>/reference_books/<reference_book_code>/<' + item_code_name + '>',
              methods=['PUT', 'DELETE'])
@remote_api_method(hook=hook)
def api_refbook_change(api_version, reference_book_code, **kwargs):
    item_code = kwargs.get(item_code_name)
    data = None
    delete = request.method == 'DELETE'
    xform = RefbookTulaXForm(api_version)
    if not delete:
        data = request.get_json()
        xform.validate(data)
        item_code = data.get(item_code_name)
    # xform.check_params(card_id, refbook_id, data)
    service_name = sys._getframe().f_code.co_name
    # т.к. на множество справочников один метод, чтобы не плодить сущности
    # прокидываем имя справочника через родительские параметры
    parents_params = {
        'rb_code': {'entity': TulaEntityCode.REFBOOK, 'id': reference_book_code},
    }
    xform.send_messages(item_code, item_code_name, data, service_name, request.method, parents_params)
