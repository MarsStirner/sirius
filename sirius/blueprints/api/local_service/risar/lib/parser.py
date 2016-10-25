#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.monitor.exception import InternalError, ExternalError


class RequestLocalData(object):
    url = None
    method = None
    # разбирает запрос локальной системы и достает полезные данные

    def __init__(self, data):
        self.validate(data)
        self.get_params(data)

    def validate(self, data):
        # todo:
        pass

    def get_params(self, data):
        self.url = data.get('url')
        self.method = data.get('method')


class LocalAnswerParser(object):
    def get_params(self, entity_code, response):
        # разбирает ответ локальной системы и достает полезные данные
        res = None
        result = self.get_data(response)['result']
        if entity_code == RisarEntityCode.CLIENT:
            res = {
                'main_id': result['client_id'],
                'param_name': 'client_id',
            }
        else:
            raise InternalError('Unexpected entity_code')
        return res

    def get_data(self, response):
        data = response.json()
        return data

    def check(self, response):
        if response.status_code != 200:
            try:
                j = response.json()
                meta = j['meta']
                if 'errors' in meta:
                    message = u'{0}: {1}. Errors: {2}. Traceback: {3}'.format(meta['code'], meta['name'], meta['errors'], meta['traceback'])
                else:
                    message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
            except Exception, e:
                message = u'Unknown ({0})({1})({2})'.format(unicode(response), unicode(response.text)[:300], unicode(e))
            raise ExternalError(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
