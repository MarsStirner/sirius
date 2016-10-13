#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from zeep import Client
from zeep.exceptions import Fault as WebFault


class MISClient(object):
    """Класс SOAP-клиента для взаимодействия с сервисом МИС"""
    def __init__(self, url, user_key):
        self.user_key = user_key
        self.client = Client(url)

    def getPatientList(self):
        try:
            result = self.client.service.searchPatient()
        except WebFault, e:
            raise
        else:
            return getattr(result, 'item', [])

    def getPatient(self):
        try:
            result = self.client.service.getPatient(
                # userKey=self.user_key,
            )
        except WebFault, e:
            raise
        else:
            return getattr(result, 'item', [])
