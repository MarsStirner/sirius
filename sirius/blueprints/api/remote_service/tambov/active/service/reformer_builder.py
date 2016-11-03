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
from sirius.models.system import SystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode

encode = WebMisJsonEncoder().default


class ServiceTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

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

        res = self.get_entity_node()
        main_item = self.set_main_entity(
            node=res,
            dst_entity_code=RisarEntityCode.MEASURE_RESEARCH,
            dst_parents_params={card_match['dst_id_url_param_name']: card_match['dst_id']},
            dst_main_id_name='result_action_id',
            src_operation_code=header_meta['remote_operation_code'],
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level=1,
            level_count=1,
        )
        main_item['body'] = {
            'result_action_id': None or Undefined,  # заполняется в set_current_id_func
            'measure_id': measure_match['dst_id'] or Undefined,
            # 'measure_type_code': service_data[''],
            # 'realization_date': service_data[''],
            # 'lpu_code': service_data[''] or Undefined,
            # 'analysis_number': service_data[''] or Undefined,
            # 'results': service_data[''],
            # 'comment': service_data[''] or Undefined,
            # 'doctor_code': service_data[''] or Undefined,
            # 'status': service_data[''] or Undefined,
        }

        return res

    ##################################################################
    ##  build packages

    def build_remote_entity_packages(self, reformed_req):
        entities = {}
        entity_packages = {
            'system_code': self.remote_sys_code,
            'entities': entities,
        }
        req_meta = reformed_req['meta']
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            api_method = ApiMethod.get(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
            )
            services_ids = self.get_services_ids(reformed_req)
            self.set_services(services_ids, entities, api_method)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            api_method = ApiMethod.get(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
            )
            self.set_services([req_meta['dst_id']], entities, api_method)
        return entity_packages

    def get_services_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_value in req['meta']['dst_parents_params'].items():
            req.setdefault('body', {}).update({param_name: param_value})
        res = self.transfer__send_request(req)
        return res

    def set_services(self, services_ids, entities, api_method):
        for service_id in services_ids:
            req = {
                'meta': {
                    'dst_method': api_method['method'],
                    'dst_url': api_method['template_url'],
                },
                'body': {
                    'id': service_id,
                }
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
