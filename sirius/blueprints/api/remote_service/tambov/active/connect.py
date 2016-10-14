#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from zeep import Client, Transport
from zeep.exceptions import Fault as WebFault

tambov_soap_login = 'ekonyaev'
tambov_soap_password = 'jW0LpcN0e'


class MISClient(object):
    """Класс SOAP-клиента для взаимодействия с сервисом МИС"""
    def __init__(self, url, user_key):
        self.user_key = user_key
        transport_with_basic_auth = Transport(
            http_auth=(tambov_soap_login, tambov_soap_password)
        )
        self.client = Client(url, transport=transport_with_basic_auth)

    def searchPatient(self):
        try:
            result = self.client.service.searchPatient(
                page=100000,
            )
        except WebFault, e:
            raise
        else:
            """
            count
            error
            patient
            """
            return getattr(result, 'patient', [])

    def getPatient(self, **kw):
        try:
            result = self.client.service.getPatient(**kw)
        except WebFault, e:
            raise
        else:
            """
            error
            patientCard
            """
            return getattr(result, 'patientCard', {})
