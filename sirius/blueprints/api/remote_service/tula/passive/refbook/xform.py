#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.lib.xform import XForm
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.refbook.schemas import \
    RefbookSchema
from sirius.models.system import SystemCode


class RefbookTulaXForm(RefbookSchema, XForm):
    remote_system_code = SystemCode.TULA
    entity_code = TulaEntityCode.REFBOOK
