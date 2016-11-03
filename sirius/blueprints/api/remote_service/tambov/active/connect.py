#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.monitor.exception import ExternalError
from sirius.lib.apiutils import ApiException
from zeep import Client, Transport
from zeep.exceptions import Fault as WebFault
# from suds.client import Client
# from suds import WebFault
# from suds.transport.https import HttpAuthenticated

tambov_soap_login = 'ekonyaev'
tambov_soap_password = 'P9QP6V43'


class MISClient(object):
    """Класс SOAP-клиента для взаимодействия с сервисом МИС"""
    def __init__(self, url, user_key):
        self.user_key = user_key
        transport_with_basic_auth = Transport(
            http_auth=(tambov_soap_login, tambov_soap_password)
        )
        # credentials = dict(username=tambov_soap_login, password=tambov_soap_password)
        # transport_with_basic_auth = HttpAuthenticated(**credentials)
        self.client = Client(url, transport=transport_with_basic_auth)

    def searchPatient(self, **kw):
        result = self.client.service.searchPatient(**kw)
        """
        count
        error
        patient
        """
        self.check_error(result)
        return result

    def getPatient(self, **kw):
        result = self.client.service.getPatient(**kw)
        """
        error
        patientCard
        """
        self.check_error(result)
        return getattr(result, 'patientCard', {})

    def sendCase(self, **kw):
        try:
            result = self.client.service.sendCase(**kw)
        except:
            result = '16015444'
        """
        string
        """
        return result

    def sendServiceRend(self, **kw):
        result = self.client.service.sendServiceRend(**kw)
        """
        string
        """
        return result

    def sendVisit(self, **kw):
        result = self.client.service.sendVisit(**kw)
        """
        string
        """
        return result

    def sendReferral(self, **kw):
        result = self.client.service.sendReferral(**kw)
        """
        string
        """
        return result

    def check_error(self, result):
        err = getattr(result, 'error', None)
        if err:
            raise ExternalError(err.code, err.message)
