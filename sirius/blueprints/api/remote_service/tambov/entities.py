#! coding:utf-8
"""


@author: BARS Group
@date: 13.10.2016

"""
from hitsl_utils.enum import Enum


class TambovEntityCode(Enum):
    PATIENT = 'patient'
    SMART_PATIENT = 'smart_patient'
    REFERRAL = 'referral'
    REND_SERVICE = 'rend_service'
    DATA_REND_SERVICE = 'data_rend_service'
    SERVICE = 'service'
    CASE = 'case'
    VISIT = 'visit'
    CLINIC = 'clinic'
    ADDRESS_ALL_INFO = 'address_all_info'
    LOCATION = 'location'
    EMPLOYEE_POSITION = 'employee_position'
    POSITION = 'position'
    EMPLOYEE = 'employee'
    INDIVIDUAL = 'individual'
    EMPLOYEE_SPECIALITIES = 'employee_specialities'
    TIME = 'time'
    BIRTH = 'birth'
    SRV_PROTOCOL = 'srv_protocol'

    # IND_ADDRESS = 'individual_address'
    # IND_DOCUMENTS = 'individual_document'
