#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.remote_service.tambov.lib.answer import TambovAnswer
from sirius.blueprints.remote_service.tambov.lib.client.connect import make_login, \
    make_api_request
from sirius.blueprints.remote_service.lib.transfer import Transfer


class TambovTransfer(Transfer):
    login = make_login
    api_request = make_api_request
    answer = TambovAnswer()
