#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.remote_service.tula.lib.answer import TulaAnswer
from sirius.blueprints.api.remote_service.tula.active.connect import make_login, \
    make_api_request
from sirius.blueprints.api.remote_service.lib.transfer import Transfer


class TulaTransfer(Transfer):
    login = make_login
    api_request = make_api_request
    answer = TulaAnswer()
