#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import requests
from hitsl_utils.enum import Enum
from requests.auth import HTTPBasicAuth
from sirius.blueprints.monitor.exception import ExternalError
from sirius.lib.apiutils import ApiException
from sirius.models.protocol import ProtocolCode
from zeep.exceptions import Fault as ZeepWebFault
from suds import WebFault as sudsWebFault

tambov_api_login = 'ekonyaev'
tambov_api_password = 'P9QP6V43'


class TambovSOAPClient(object):
    """Класс SOAP-клиента для взаимодействия с сервисом МИС"""
    def __init__(self, url, wsdl_lib_code):
        if wsdl_lib_code == 'zeep':
            self.init_zeep_lib(url)
        if wsdl_lib_code == 'suds':
            self.init_suds_lib(url)

    def init_zeep_lib(self, url):
        from zeep import Client, Transport
        transport_with_basic_auth = Transport(
            http_auth=(tambov_api_login, tambov_api_password)
        )

        self.client = Client(url, transport=transport_with_basic_auth)

    def init_suds_lib(self, url):
        from suds.client import Client
        from suds.transport.https import HttpAuthenticated
        credentials = dict(username=tambov_api_login, password=tambov_api_password)
        transport_with_basic_auth = HttpAuthenticated(**credentials)

        self.client = Client(url, transport=transport_with_basic_auth)

    def check_error(self, result):
        err = getattr(result, 'error', None)
        if err:
            raise ExternalError(err.code, err.message)

    def searchPatient(self, **kw):
        result = self.client.service.searchPatient(**kw)
        """
        count
        error
        patient
        """
        self.check_error(result)
        return result

    def getPatient_Smart(self, **kw):
        result = self.client.service.getPatient(**kw)
        """
        error
        patientCard
        """
        self.check_error(result)
        return getattr(result, 'patientCard', {})


class RequestModeCode(Enum):
    MULTIPART_FILE = 'multipart_file'
    JSON_DATA = 'json_data'


class TambovRESTClient(object):
    basic_auth = HTTPBasicAuth(tambov_api_login, tambov_api_password)

    def make_login(self):
        # token = get_token(login, password)
        # print ' > auth token: ', token
        # session_token = get_role(token)
        # print ' > session token: ', session_token
        # session = token, session_token
        session = None, None

        return session

    def make_api_request(self, method, url, session,
                         any_data=None, url_args=None, req_mode=None):
        authent_token, authoriz_token = session
        data_type = 'json'
        if req_mode == RequestModeCode.MULTIPART_FILE:
            data_type = 'files'
        # if protocol == ProtocolCode.SOAP:
        #     data_type = 'data'
        response = getattr(requests, method)(
            url,
            params=url_args,
            auth=self.basic_auth,
            # cookies={authent_token_name: authent_token,
            #          authoriz_token_name: authoriz_token}
            **{data_type: any_data}
        )
        return response
