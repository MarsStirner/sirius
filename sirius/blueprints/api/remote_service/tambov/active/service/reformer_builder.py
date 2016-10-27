#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.remote_system import RemoteSystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode


class ServiceTambovBuilder(Builder):
    remote_sys_code = RemoteSystemCode.TAMBOV

    ##################################################################
    ##  reform entities client

    def build_local_measure(self, header_meta, entity_package, addition_data):
        service_data = entity_package['data']
        if service_data.type == 11:
            res = self.build_local_measure_research(header_meta, service_data)
        elif service_data.type == 12:
            res = self.build_local_measure_specialists_checkup(header_meta, service_data)
        elif service_data.type == 13:
            res = self.build_local_measure_hospitalization(header_meta, service_data)
        else:
            # todo:
            raise NotImplementedError()
        return res

    def build_local_measure_research(self, header_meta, service_data):
        src_entity_code = header_meta['remote_entity_code']

        card_match = MatchingId.first_local_id(
            TambovEntityCode.PATIENT,
            service_data['patient_uid'],
            RisarEntityCode.CARD,
            self.remote_sys_code,
        )
        measure_match = MatchingId.first_local_id(
            TambovEntityCode.REFERRAL,
            service_data['referralId'],
            RisarEntityCode.MEASURE,
            self.remote_sys_code,
        )

        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'].update({
                'result_action_id': reform_meta['dst_id'] or Undefined,
            })
        res = {
            'operation_order': {},
            RisarEntityCode.MEASURE_RESEARCH: [{
                'meta': {
                    'src_operation_code': header_meta['remote_operation_code'],
                    'src_entity_code': src_entity_code,
                    'src_id': header_meta['remote_main_id'],
                    'dst_entity_code': RisarEntityCode.MEASURE_RESEARCH,
                    'dst_parents_params': {card_match['dst_id_url_param_name']: card_match['dst_id']},
                    'set_current_id_func': set_current_id_func,
                },
            }],
        }
        main_item = res[RisarEntityCode.MEASURE_RESEARCH][0]
        self.set_operation_order(res, RisarEntityCode.MEASURE_RESEARCH, 1)
        main_item['body'] = {
            'result_action_id': None or Undefined,  # заполняется в set_current_id_func
            'measure_id': measure_match['dst_id'] or Undefined,
            'measure_type_code': service_data[''],
            'realization_date': service_data[''],
            'lpu_code': service_data[''] or Undefined,
            'analysis_number': service_data[''] or Undefined,
            'results': service_data[''],
            'comment': service_data[''] or Undefined,
            'doctor_code': service_data[''] or Undefined,
            'status': service_data[''] or Undefined,
        }

        return res

    ##################################################################
    ##  reform service requests

    def build_remote_service_request(self, header_meta):
        req_data = {
            'meta': {
                'src_entity_code': header_meta['local_entity_code'],
                'src_id': header_meta['local_main_id'],
                'src_parents_params': header_meta['local_parents_params'],
                'dst_system_code': self.remote_sys_code,
                'dst_entity_code': TambovEntityCode.SERVICE,
                'dst_operation_code': header_meta['local_operation_code'],
                'dst_id': header_meta['remote_main_id'],
            }
        }
        return req_data

    ##################################################################
    ##  build packages patient

    def build_remote_service_entity_packages(self, reformed_req):
        entities = {}
        entity_packages = {
            'system_code': self.remote_sys_code,
            'entities': entities,
        }
        req_meta = reformed_req['meta']
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            api_method = ApiMethod.get_method(
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
                self.remote_sys_code,
            )
            services_ids = self.get_services_ids(reformed_req)
            self.set_services(services_ids, entities, api_method)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            api_method = ApiMethod.get_method(
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
                self.remote_sys_code,
            )
            self.set_services([req_meta['dst_id']], entities, api_method)
        return entity_packages

    def get_services_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_value in req['meta']['dst_parents_params'].items():
            req['meta'].setdefault('dst_id_url_param_name', []).append(param_name)
            req['meta'].setdefault('dst_id', []).append(param_value)
        res = self.transfer__send_request(req)
        return res

    def set_services(self, services_ids, entities, api_method):
        for service_id in services_ids:
            req = {
                'meta': {
                    'dst_method': api_method['method'],
                    'dst_url': api_method['template_url'],
                    'dst_id_url_param_name': 'id',
                    'dst_id': service_id,
                },
            }
            service_data = self.transfer__send_request(req)
            root_parent = service_node = {
                'is_changed': False,
                'method': req['meta']['dst_method'],
                'main_id': service_id,
                'data': service_data,
            }
            entities.setdefault(
                TambovEntityCode.SERVICE, []
            ).append(service_node)
