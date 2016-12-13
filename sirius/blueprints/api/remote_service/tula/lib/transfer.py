#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""

from sirius.blueprints.api.remote_service.tula.active.connect import \
    TulaRESTClient
from sirius.blueprints.api.remote_service.tula.lib.answer import TulaAnswer
from sirius.blueprints.api.remote_service.lib.transfer import Transfer
from sirius.blueprints.monitor.exception import connect_entry


class TulaTransfer(Transfer):
    answer = TulaAnswer()

    def get_rest_client(self):
        rest_client_code = 'rest'
        if rest_client_code not in self.clients:
            self.clients[rest_client_code] = TulaRESTClient()
        return self.clients[rest_client_code]
