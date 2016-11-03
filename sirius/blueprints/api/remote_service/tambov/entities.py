#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from hitsl_utils.enum import Enum


class TambovEntityCode(Enum):
    PATIENT = 'patient'
    REFERRAL = 'referral'
    SERVICE = 'service'
    CASE = 'case'
    VISIT = 'visit'

    # IND_ADDRESS = 'individual_address'
    # IND_DOCUMENTS = 'individual_document'
