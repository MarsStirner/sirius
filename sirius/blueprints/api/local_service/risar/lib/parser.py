#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.app import app
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.monitor.exception import InternalError, ExternalError
from sirius.models.system import RegionCode, SystemCode, Host


class RequestLocalData(object):
    service_method = None
    entity_code = None
    operation_code = None
    request_url = None
    request_method = None
    request_params = None
    method = None
    main_id = None
    main_param_name = None
    body = None
    stream_id = None
    # разбирает запрос локальной системы и достает полезные данные

    def __init__(self, data):
        self.validate(data)
        self.get_params(data)
        self.data = data

        system_code = {
            RegionCode.TAMBOV: SystemCode.TAMBOV,
        }
        # todo: ух
        remote_entity_map = {
            'patient': 'smart_patient',
        }
        if self.data.get('remote_system_code'):
            self.data['remote_system_code'] = system_code[self.data.get('remote_system_code')]
        if self.data.get('remote_entity_code'):
            self.data['remote_entity_code'] = remote_entity_map[self.data.get('remote_entity_code')]

    def validate(self, data):
        # todo:
        pass

    def get_params(self, data):
        if data.get('request_url'):
            if data.get('request_url').startswith('http:'):
                self.request_url = data.get('request_url')
            else:
                self.request_url = (Host.get_url(SystemCode.LOCAL).rstrip('/') + data.get('request_url'))
        self.request_method = data.get('request_method')

        self.entity_code = data.get('entity_code')
        self.operation_code = data.get('operation_code')
        self.service_method = data.get('service_method')
        self.request_params = data.get('request_params')
        self.method = data.get('method')
        self.main_id = data.get('main_id')
        self.main_param_name = data.get('main_param_name')
        self.body = data.get('data')
        self.stream_id = data.get('stream_id')

    def get_msg_meta(self):
        meta = {
            'local_service_code': self.service_method,
            'local_entity_code': self.entity_code,
            'local_operation_code': self.operation_code,
            'local_main_id': self.main_id,
            'local_main_param_name': self.main_param_name,
            'local_method': self.method,
            'local_parents_params': dict((k, {'id': v}) for k, v in self.request_params.items()),
        }
        return meta


class LocalAnswerParser(object):
    def get_params(self, entity_code, response, param_name):
        # разбирает ответ локальной системы и достает полезные данные
        res = None
        result = self.get_data(response)
        if entity_code == RisarEntityCode.CLIENT and response.status_code == 409:
            # для Тулы первичная посадка пациентов, которые есть в МР, но нет в шине
            # если придет реальный дубль, то он сядет в matching_id и следующие PUT будут падать
            j = response.json()
            client_id = j['meta']['client_id']
            res = {
                'main_id': client_id,
                'param_name': param_name,
            }
            return res

        elif entity_code == RisarEntityCode.CLIENT:

            param_name = 'client_id'
            res = {
                'main_id': result[param_name],
                'param_name': param_name,
            }
        else:
            if param_name in result:
                res = {
                    'main_id': result[param_name],
                    'param_name': param_name,
                }
        return res

    def get_data(self, response):
        try:
            data = response.json()
            res = data['result']
        except ValueError:
            res = response.text
        return res

    def check(self, response):
        if response.status_code != 200:

            # для Тулы первичная посадка пациентов, которые есть в МР, но нет в шине
            if response.status_code == 409 and app.config.get('REGION_CODE') == 'tula':
                return

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
            raise ExternalError(unicode(u'Api Error: {0}'.format(message)))
