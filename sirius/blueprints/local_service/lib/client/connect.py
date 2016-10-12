#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

Соединение и отправка запроса в API РИСАР (hippocrate)
"""

import requests
from sirius.app import app

from contextlib import contextmanager

config = app.config
hippo_url = config.get('HIPPOCRATE_URL', 'http://127.0.0.1:6600/').rstrip('/')
coldstar_url = config.get('COLDSTAR_URL', 'http://127.0.0.1:6605/').rstrip('/')
api_login = config.get('HIPPOCRATE_API_LOGIN', u'ВнешСис')
api_password = config.get('HIPPOCRATE_API_PASSWORD', '')
api_auth_token_name = config.get('CASTIEL_AUTH_TOKEN', 'CastielAuthToken')
api_session_token_name = config.get('HIPPOCRATE_SESSION_KEY', 'hippocrates.session.id')


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
        raise Exception(j['exception'])
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
        raise Exception(j['exception'])


def get_role(token, role_code=''):
    url = u'%s/chose_role/' % hippo_url
    if role_code:
        url += role_code
    result = requests.post(
        url,
        cookies={api_auth_token_name: token}
    )
    j = result.json()
    if not result.status_code == 200:
        raise Exception('Ошибка авторизации')
    return result.cookies[api_session_token_name]


@contextmanager
def make_login():
    token = get_token(api_login, api_password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
    session = token, session_token

    try:
        yield session
    finally:
        release_token(token)


def make_api_request(method, url, session, json_data=None, url_args=None):
    token, session_token = session
    print url
    result = getattr(requests, method)(
        url,
        json=json_data,
        params=url_args,
        cookies={api_auth_token_name: token,
                 api_session_token_name: session_token}
    )
    if result.status_code != 200:
        try:
            j = result.json()
            message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
        except Exception, e:
            # raise e
            message = u'Unknown ({0})'.format(unicode(result))
        raise Exception(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
    return result.json()


def test_auth(login, password):
    print 'Coldstar: ', coldstar_url, ', Risar: ', hippo_url
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
    release_token(token)
