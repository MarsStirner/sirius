#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""

import os
import requests

from contextlib import contextmanager


auth_token_name = 'CastielAuthToken'
session_token_name = 'hippocrates.session.id'

login = os.getenv('TEST_LOGIN', u'ВнешСис')
password = os.getenv('TEST_PASSWORD', '0909')


def get_hippo_url():
    from sirius.app import app
    mis_url = app.config.get('HIPPOCRATE_URL', 'http://127.0.0.1:6600/')
    return mis_url.rstrip('/')


def get_coldstar_url():
    from sirius.app import app
    cs_url = app.config.get('COLDSTAR_URL', 'http://127.0.0.1:6605/')
    return cs_url.rstrip('/')


def get_token(login, password):
    url = u'%s/cas/api/acquire' % get_coldstar_url()
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
    url = u'%s/cas/api/release' % get_coldstar_url()
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
    url = u'%s/chose_role/' % get_hippo_url()
    if role_code:
        url += role_code
    result = requests.post(
        url,
        cookies={auth_token_name: token}
    )
    j = result.json()
    if not result.status_code == 200:
        raise Exception('Ошибка авторизации')
    return result.cookies['hippocrates.session.id']


@contextmanager
def make_login():
    token = get_token(login, password)
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
    result = getattr(requests, method)(
        get_hippo_url() + url,
        json=json_data,
        params=url_args,
        cookies={auth_token_name: token,
                 session_token_name: session_token}
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
    print 'Coldstar: ', get_coldstar_url(), ', Risar: ', get_hippo_url()
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
