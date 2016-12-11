#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from contextlib import contextmanager

from sirius.blueprints.api.remote_service.tula.active.connect import \
    TulaRESTClient
from sirius.blueprints.api.remote_service.tula.lib.answer import TulaAnswer
from sirius.blueprints.api.remote_service.lib.transfer import Transfer


class TulaTransfer(Transfer):
    answer = TulaAnswer()

    def __init__(self):
        self.client = TulaRESTClient()
        self.api_request = self.client.make_api_request

    @contextmanager
    def login(self):
        try:
            yield self.client.make_login()
        finally:
            pass
