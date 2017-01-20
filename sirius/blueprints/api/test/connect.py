# coding: utf-8

import requests
from sirius.app import app

from contextlib import contextmanager

from sirius.blueprints.monitor.exception import ConnectError, ExternalError

config = app.config
hippo_url = config.get('HIPPOCRATE_URL', 'http://127.0.0.1:6600/').rstrip('/')
sirius_url = config.get('SIRIUS_URL', 'http://127.0.0.1:8600/').rstrip('/')
coldstar_url = config.get('COLDSTAR_URL', 'http://127.0.0.1:6605/').rstrip('/')
login = config.get('HIPPOCRATE_API_LOGIN', u'ВнешСис')
password = config.get('HIPPOCRATE_API_PASSWORD', '')
authent_token_name = config.get('CASTIEL_AUTH_TOKEN', 'CastielAuthToken')
authoriz_token_name = config.get('HIPPOCRATE_SESSION_KEY', 'hippocrates.session.id')


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
    # пока роль не запрашиваем
    return 'role-token'
    # url = u'%s/chose_role/' % sirius_url
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
        pass
        # release_token(token)


def get_req_method(testapp, method):
    res = None
    if method == 'post':
        res = testapp.post_json
    elif method == 'put':
        res = testapp.put_json
    elif method == 'delete':
        res = testapp.delete_json
    return res


def make_api_request(method, url, session, json_data=None, url_args=None):
    token, session_token = session
    print sirius_url + url
    result = getattr(requests, method)(
        sirius_url + url,
        json=json_data,
        params=url_args,
        cookies={authent_token_name: token,
                 authoriz_token_name: session_token}
    )
    # if result.status_code != 200:
    #     try:
    #         j = result.json()
    #         message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
    #     except Exception, e:
    #         # raise e
    #         message = u'Unknown ({0})({1})({2})'.format(unicode(result), unicode(result.text)[:300], unicode(e))
    #     raise Exception(unicode(u'Api Error: {0}'.format(message)))
    return result.json()


def make_test_api_request(testapp, method, url, session, json_data=None, url_args=None):
    token, session_token = session
    result = get_req_method(testapp, method)(
        sirius_url + url,
        json_data,
        # params=url_args,
        # cookies={authent_token_name: token,
        #          authoriz_token_name: session_token}
    )
    if result.status_code != 200:
        try:
            j = result.json()
            message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
        except Exception, e:
            # raise e
            message = u'Unknown ({0})({1})'.format(unicode(result), unicode(e))
        raise ExternalError(unicode(u'Api Error: {0}'.format(message)))
    res = result.json
    if callable(res):
        res = res()
    return res


def test_auth(login, password):
    print 'Coldstar: ', coldstar_url, ', Risar: ', sirius_url
    token = get_token(login, password)
    print ' > auth token: ', token
    session_token = get_role(token)
    print ' > session token: ', session_token
