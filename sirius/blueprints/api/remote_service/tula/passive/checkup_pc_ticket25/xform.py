#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.lib.xform import XForm
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.checkup_first_ticket25.schemas import \
    CheckupsTicket25XFormSchema
from sirius.models.system import SystemCode


class CheckupFirstTicket25TulaXForm(CheckupsTicket25XFormSchema, XForm):
    remote_system_code = SystemCode.TULA
    entity_code = TulaEntityCode.CHECKUP_OBS_FIRST_TICKET
