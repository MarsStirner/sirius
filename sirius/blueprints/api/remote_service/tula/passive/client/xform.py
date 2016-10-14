#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.lib.xform import XForm
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.client.schemas import \
    ClientSchema
from sirius.lib.remote_system import RemoteSystemCode


class TulaClientXForm(ClientSchema, XForm):
    remote_system_code = RemoteSystemCode.TULA
    entity_code = TulaEntityCode.CLIENT
