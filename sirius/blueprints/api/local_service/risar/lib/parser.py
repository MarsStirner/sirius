#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.monitor.exception import InternalError, ExternalError


class RequestLocalData(object):
    service_method = None
    request_url = None
    request_method = None
    request_params = None
    method = None
    main_id = None
    main_param_name = None
    # разбирает запрос локальной системы и достает полезные данные

    def __init__(self, data):
        self.validate(data)
        self.get_params(data)
        self.data = data

    def validate(self, data):
        # todo:
        pass

    def get_params(self, data):
        self.request_url = data.get('request_url')
        self.request_method = data.get('request_method')

        self.service_method = data.get('service_method')
        self.request_params = data.get('request_params')
        self.method = data.get('method')
        self.main_id = data.get('main_id')
        self.main_param_name = data.get('main_param_name')

    def get_msg_meta(self):
        meta = {
            'local_service_code': self.service_method,
            'local_main_id': self.main_id,
            'local_main_param_name': self.main_param_name,
            'local_method': self.method,
            'local_parents_params': dict((k, {'id': v}) for k, v in self.request_params.items()),
        }
        return meta


class LocalAnswerParser(object):
    def get_params(self, entity_code, response, param_name):
        # разбирает ответ локальной системы и достает полезные данные
        result = self.get_data(response)
        if entity_code == RisarEntityCode.CLIENT:
            param_name = 'client_id'
            res = {
                'main_id': result[param_name],
                'param_name': param_name,
            }
        else:
            res = {
                'main_id': result[param_name],
                'param_name': param_name,
            }
        return res

    def get_data(self, response):
        data = response.json()
        return data['result']

    def check(self, response):
        if response.status_code != 200:
            try:
                j = response.json()
                meta = j['meta']
                if 'errors' in meta:
                    message = u'{0}: {1}. Errors: {2}. Traceback: {3}'.format(meta['code'], meta['name'], meta['errors'], meta['traceback'])
                elif 'reason' in meta:
                    message = u'{0}: {1}. Reason: {2}. Traceback: {3}'.format(meta['code'], meta['name'], meta['reason'], meta['traceback'])
                else:
                    message = u'{0}: {1}'.format(j['meta']['code'], j['meta']['name'])
            except Exception, e:
                message = u'Unknown ({0})({1})({2})'.format(unicode(response), unicode(response.text)[:300], unicode(e))
            raise ExternalError(unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
