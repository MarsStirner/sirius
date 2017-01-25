#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

Соединение и отправка запроса в API РИСАР (hippocrate)
"""

import requests
from sirius.app import app

from contextlib import contextmanager

from sirius.blueprints.monitor.exception import ExternalError, ConnectError

config = app.config
hippo_url = config.get('HIPPOCRATE_URL', 'http://127.0.0.1:6600/').rstrip('/')
coldstar_url = config.get('COLDSTAR_URL', 'http://127.0.0.1:6605/').rstrip('/')
login = config.get('HIPPOCRATE_API_LOGIN', u'ВнешСис')
password = config.get('HIPPOCRATE_API_PASSWORD', '')
authent_token_name = config.get('CASTIEL_AUTH_TOKEN', 'CastielAuthToken')
authoriz_token_name = config.get('HIPPOCRATE_SESSION_KEY', 'hippocrates.session.id')
session = None


def get_token(login, password):
    url = u'%s/cas/api/acquire' % coldstar_url
    result = requests.post(
        url,
        {
            'login': login,
            'password': password
        }
    )
    j = result.json()
    if not j['success']:
        print j
        raise ConnectError(j['exception'])
    return j['token']


def release_token(token):
    url = u'%s/cas/api/release' % coldstar_url
    result = requests.post(
        url,
        {
            'token': token,
        }
    )
    j = result.json()
    if not j['success']:
        print j
        raise ExternalError(j['exception'])


def get_role(token, role_code=''):
    url = u'%s/chose_role/' % hippo_url
    if role_code:
        url += role_code
    result = requests.post(
        url,
        cookies={authent_token_name: token}
    )
    j = result.json()
    if not result.status_code == 200:
        raise ConnectError(u'Ошибка авторизации')
    return result.cookies[authoriz_token_name]


def make_login():
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
    session = token, session_token

    return session


def make_api_request(method, url, session, json_data=None, url_args=None):
    authent_token, authoriz_token = session
    # todo: если используется внешний cas, добавлять постфикс (параметр в конф)
    response = getattr(requests, method)(
        url + '?dont_check_tgt=true',
        json=json_data,
        params=url_args,
        cookies={authent_token_name: authent_token,
                 authoriz_token_name: authoriz_token}
    )
    return response


def test_auth(login, password):
    print 'Coldstar: ', coldstar_url, ', Risar: ', hippo_url
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
    release_token(token)
