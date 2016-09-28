#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from sirius.blueprints.remote_service.lib.tambov.reformer import TambovReformer
from sirius.blueprints.remote_service.lib.tambov.transfer import TambovTransfer
from sirius.blueprints.remote_service.lib.tula.reformer import TulaReformer
from sirius.blueprints.remote_service.lib.tula.transfer import TulaTransfer


class Implementation(object):
    def get_reformer(self, rmt_sys_code):
        if rmt_sys_code == '':
            reformer = TambovReformer()
        elif rmt_sys_code == '':
            reformer = TulaReformer()
        else:
            raise Exception('Unknown remote code')
        return reformer

    def get_transfer(self, rmt_sys_code):
        if rmt_sys_code == '':
            transfer = TambovTransfer()
        elif rmt_sys_code == '':
            transfer = TulaTransfer()
        else:
            raise Exception('Unknown remote code')
        return transfer
