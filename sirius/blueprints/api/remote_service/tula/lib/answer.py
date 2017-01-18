#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer
import xml.etree.ElementTree as ET

from sirius.blueprints.api.remote_service.lib.transfer import \
    RequestModeCode
from sirius.blueprints.api.remote_service.tula.entities import TulaEntityCode
from sirius.blueprints.monitor.exception import ExternalError
from sirius.lib.apiutils import ApiException
from sirius.models.operation import OperationCode


class TulaAnswer(RemoteAnswer):

    def xml_to_dict(self, result):
        e = ET.XML(result.text)
        return e

    def get_params_ext(self, req_meta, req_result):
        entity_code = req_meta['dst_entity_code']
        dst_operation_code = req_meta['dst_operation_code']
        param_name = req_meta['dst_id_url_param_name']
        if entity_code == TulaEntityCode.SCHEDULE_TICKET:
            find_prefix = './/{http://sdsys.ru/}'
            res = req_result.findtext(find_prefix + 'SPRESULT')
            if res != '1':
                res_comment = req_result.findtext(find_prefix + 'SPCOMMENT') or ''
                if dst_operation_code != OperationCode.DELETE:
                    op_name = 'reserve'
                else:
                    op_name = 'remove'
                raise ApiException(
                    200, 'Reject %s ticket %s. Result code = %s comment: %s' % (
                        op_name, req_meta['dst_main_id'],
                        res, res_comment
                    ),
                    reject=1,
                )
            if dst_operation_code != OperationCode.DELETE:
                schedid = req_result.findtext(find_prefix + 'RSCHEDID')
                res = {
                    'main_id': schedid,
                    'param_name': param_name,
                }
            else:
                res = True
        else:
            res = req_result
        return res

    def get_params(self, entity_code, response, param_name):
        # разбирает ответ локальной системы и достает полезные данные
        result = self.get_data(response)
        if entity_code == TulaEntityCode.CLIENT:
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
        try:
            data = response.json()
            res = data['result']
        except ValueError:
            res = response.text
        return res

    def check_json(self, response):
        if response.status_code != 200:
            try:
                j = response.json()
                meta = j['meta']
                if 'errors' in meta:
                    message = u'{0}: {1}. Errors: {2}. Traceback: {3}'.format(
                        meta['code'], meta['name'], meta['errors'],
                        meta['traceback'])
                elif 'reason' in meta:
                    message = u'{0}: {1}. Reason: {2}. Traceback: {3}'.format(
                        meta['code'], meta['name'], meta['reason'],
                        meta['traceback'])
                else:
                    message = u'{0}: {1}'.format(j['meta']['code'],
                                                 j['meta']['name'])
            except Exception, e:
                message = u'Unknown ({0})({1})({2})'.format(unicode(response),
                                                            unicode(response.text)[
                                                            :300], unicode(e))
            raise ExternalError(
                unicode(u'Api Error: {0}'.format(message)).encode('utf-8'))
