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
    CLINIC = 'clinic'
    ADDRESS_ALL_INFO = 'address_all_info'
    LOCATION = 'location'
    EMPLOYEE_POSITION = 'employee_position'
    EMPLOYEE = 'employee'
    INDIVIDUAL = 'individual'
    EMPLOYEE_SPECIALITIES = 'employee_specialities'
    TIME = 'time'

    # IND_ADDRESS = 'individual_address'
    # IND_DOCUMENTS = 'individual_document'
