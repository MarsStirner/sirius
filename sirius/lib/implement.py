#! coding:utf-8
"""


@author: BARS Group
@date: 27.09.2016

"""
from sirius.blueprints.local_service.lib.entities import LocalEntity
from sirius.blueprints.remote_service.lib.tambov.reformer import TambovReformer
from sirius.blueprints.remote_service.lib.tambov.transfer import TambovTransfer
from sirius.blueprints.remote_service.lib.tula.reformer import TulaReformer
from sirius.blueprints.remote_service.lib.tula.transfer import TulaTransfer


implements = (
    (TambovReformer, TambovTransfer),
    (TulaReformer, TulaTransfer),
)

# страхуемся от копипасты (ошибок)
imp_map = {}
for imp in implements:
    sys_code = imp[0].remote_sys_code
    if sys_code not in imp_map:
        imp_map[sys_code] = imp
    else:
        raise RuntimeError('Duplicate remote_sys_code')


class Implementation(object):
    def get_reformer(self, rmt_sys_code):
        try:
            reformer_cls, transfer_cls = imp_map[rmt_sys_code]
        except KeyError:
            raise Exception('Unknown remote code "%s" in implements' % rmt_sys_code)
        reformer = reformer_cls()
        reformer.set_transfer(transfer_cls())
        reformer.set_local_entity_enum(LocalEntity)
        return reformer
