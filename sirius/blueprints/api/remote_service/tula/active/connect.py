#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
import requests
from sirius.blueprints.api.remote_service.tambov.active.connect import \
    RequestModeCode


class TulaRESTClient(object):
    # basic_auth = HTTPBasicAuth(tambov_api_login, tambov_api_password)

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
        if req_mode == RequestModeCode.XML_DATA:
            data_type = 'data'
        response = getattr(requests, method)(
            url,
            params=url_args,
            # auth=self.basic_auth,
            # cookies={authent_token_name: authent_token,
            #          authoriz_token_name: authoriz_token}
            **{data_type: any_data}
        )
        return response
