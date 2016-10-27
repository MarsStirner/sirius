#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from hitsl_utils.enum import Enum


class RisarEntityCode(Enum):
    CLIENT = 'client'
    CARD = 'card'
    MEASURE = 'measure'
    MEASURE_RESEARCH = 'measure_research'
    MEASURE_HOSPITALIZATION = 'measure_hospitalization'
    MEASURE_SPECIALISTS_CHECKUP = 'measure_specialists_checkup'

    CHECKUP_OBS_FIRST = 'checkup_obs_first'
