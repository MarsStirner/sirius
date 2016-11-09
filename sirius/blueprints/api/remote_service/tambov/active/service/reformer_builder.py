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
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities
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
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

    ##################################################################
    ##  reform entities client

    def build_local_measure(self, header_meta, pack_entity, addition_data):
        service_data = pack_entity['data']
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
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.PATIENT: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            }
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        # card_match = MatchingId.first_local_id(
        #     TambovEntityCode.PATIENT,
        #     service_data['patient_uid'],
        #     RisarEntityCode.CARD,
        #     self.remote_sys_code,
        # )
        measure_match = MatchingId.first_local_id(
            TambovEntityCode.REFERRAL,
            service_data['referralId'],
            RisarEntityCode.MEASURE,
            self.remote_sys_code,
        )

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.MEASURE_RESEARCH,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='result_action_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level=1,
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                # 'result_action_id': None,  # заполняется в set_current_id_func
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

        return entities

    ##################################################################
    ##  build packages

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self.remote_sys_code)
        req_meta = reformed_req['meta']
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
            )
            services_ids = self.get_services_ids(reformed_req)
            self.set_services(services_ids, package, api_method, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
            )
            self.set_services([req_meta['dst_id']], package, api_method, req_meta)
        return package

    def get_services_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_value in req['meta']['dst_parents_params'].items():
            req.setdefault('body', {}).update({param_name: param_value})
        res = self.transfer__send_request(req)
        return res

    def set_services(self, services_ids, package, api_method, req_meta):
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
            main_item = package.add_main_pack_entity(
                entity_code=TambovEntityCode.SERVICE,
                method=req['meta']['dst_method'],
                main_param_name='measure_id',
                main_id=service_id,
                parents_params=req_meta['dst_parents_params'],
                data=service_data,
            )
