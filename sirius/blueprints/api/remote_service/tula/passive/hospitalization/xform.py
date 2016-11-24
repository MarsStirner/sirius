#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from sirius.lib.xform import XForm
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.api.remote_service.tula.passive.hospitalization.schemas import \
    HospitalizationSchema
from sirius.models.system import SystemCode


class HospitalizationTulaXForm(HospitalizationSchema, XForm):
    remote_system_code = SystemCode.TULA
    entity_code = TulaEntityCode.MEASURE_HOSPITALIZATION
