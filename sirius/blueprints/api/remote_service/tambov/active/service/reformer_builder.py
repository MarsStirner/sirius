#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.models.system import SystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode

encode = WebMisJsonEncoder().default
to_date = lambda x: datetime.strptime(x, '%Y-%m-%d')


class ServiceTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid'
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

    ##################################################################
    ##  build packages

    def build_remote_entity_packages(self, reformed_req):
        """
        Сборка услуг с направлениями. Уже здесь направление делаем родительским,
        т.к. список сущностей разбивается на сообщения, в которых нужно решать,
        что делать с направлением.
        """
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            services_ids = self.get_services_ids(reformed_req)
            self.set_services(services_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_services([req_meta['dst_id']], package, req_meta)
        return package

    def get_services_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({param_name: param_data['id']})
        res = self.transfer__send_request(req)
        return res

    def set_services(self, rend_services_ids, package, req_meta):
        rend_serv_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.REND_SERVICE,
            OperationCode.READ_ONE,
        )
        referral_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.REFERRAL,
            OperationCode.READ_ONE,
        )

        referral_items = {}
        for rend_service_id in rend_services_ids:
            req = DataRequest()
            req.set_req_params(
                url=rend_serv_api_method['template_url'],
                method=rend_serv_api_method['method'],
                data={'id': rend_service_id},
            )
            rend_service_data = self.transfer__send_request(req)
            referralId = rend_service_data['referralId']
            # так как в мис направление не указано, а в мр его нужно создать
            # обозначим направление мис фейковым ID. если в мис проставят
            # направление, то в мр должны создать новое и перепривязать услугу
            if referralId:
                req = DataRequest()
                req.set_req_params(
                    url=referral_api_method['template_url'],
                    method=referral_api_method['method'],
                    data={'id': referralId},
                )
                referral_data = self.transfer__send_request(req)
            else:
                continue
                if not rend_service_data['prototypeId']:
                    continue
                referralId = '_'.join(('rend_serviceId', rend_service_id))
                referral_data = {}

            if referralId in referral_items:
                main_item = referral_items[referralId]
            else:
                main_item = package.add_main_pack_entity(
                    entity_code=TambovEntityCode.REFERRAL,
                    method=req.method,
                    main_param_name='id',
                    main_id=referralId,
                    parents_params=req_meta['dst_parents_params'],
                    data=referral_data,
                )
                referral_items[referralId] = main_item

            send_srv_item = package.add_child_pack_entity(
                root_item=main_item,
                parent_item=main_item,
                entity_code=TambovEntityCode.REND_SERVICE,
                method=req.method,
                main_id=rend_service_id,
                data=rend_service_data,
            )

    # todo: удалить, когда объединение запланированных и внеплановых утвердится
# class ServiceTambovBuilder__(Builder):
#     remote_sys_code = SystemCode.TAMBOV
#
#     ##################################################################
#     ##  reform requests
#
#     def build_remote_request(self, header_meta, dst_entity_code):
#         # сопоставление параметров родительских сущностей
#         src_entity_code = header_meta['local_entity_code']
#         params_map = {
#             RisarEntityCode.CARD: {
#                 'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid'
#             },
#             RisarEntityCode.MEASURE: {
#                 'entity': TambovEntityCode.REFERRAL, 'param': 'referralId'
#             },
#         }
#         self.reform_local_parents_params(header_meta, src_entity_code, params_map)
#
#         req_data = self.build_remote_request_common(header_meta, dst_entity_code)
#         return req_data
#
#     ##################################################################
#     ##  reform entities client
#
#     def build_local_measure(self, header_meta, pack_entity):
#         service_data = pack_entity['data']
#         srv_prototype__measure_type__map = {
#             '5338': 'lab_test',
#             '5339': 'func_test',
#         }
#         measure_type = srv_prototype__measure_type__map[service_data.prototypeId]
#         research_meas_types = ('lab_test', 'func_test')
#         checkup_meas_types = ('checkup',)
#         if measure_type in research_meas_types:
#             res = self.build_local_measure_research(header_meta, service_data, measure_type)
#         elif measure_type in checkup_meas_types:
#             res = self.build_local_measure_specialists_checkup(header_meta, service_data, measure_type)
#         else:
#             # todo:
#             raise NotImplementedError()
#         return res
#
#     def build_local_measure_research(self, header_meta, service_data, measure_type):
#         src_entity_code = header_meta['remote_entity_code']
#         src_operation_code = header_meta['remote_operation_code']
#
#         # сопоставление параметров родительских сущностей
#         params_map = {
#             TambovEntityCode.SMART_PATIENT: {
#                 'entity': RisarEntityCode.CARD, 'param': 'card_id'
#             },
#             TambovEntityCode.REFERRAL: {
#                 'entity': RisarEntityCode.MEASURE, 'param': 'measure_id'
#             },
#         }
#         self.reform_remote_parents_params(header_meta, src_entity_code, params_map)
#
#         entities = RequestEntities()
#         main_item = entities.set_main_entity(
#             dst_entity_code=RisarEntityCode.MEASURE_RESEARCH,
#             dst_parents_params=header_meta['local_parents_params'],
#             dst_main_id_name='result_action_id',
#             src_operation_code=src_operation_code,
#             src_entity_code=src_entity_code,
#             src_main_id_name=header_meta['remote_main_param_name'],
#             src_id=header_meta['remote_main_id'],
#             level_count=1,
#         )
#         if src_operation_code != OperationCode.DELETE:
#             main_item['body'] = {
#                 # 'result_action_id': None,  # заполняется в set_current_id_func
#                 'measure_id': str(header_meta['local_parents_params']['measure_id']['id']),
#                 'measure_type_code': measure_type,
#                 'realization_date': to_date(service_data['dateTo']),
#                 # 'lpu_code': service_data[''] or Undefined,
#                 # 'analysis_number': service_data[''] or Undefined,
#                 'results': service_data[''],
#                 # 'comment': service_data[''] or Undefined,
#                 # 'doctor_code': service_data[''] or Undefined,
#                 # 'status': service_data[''] or Undefined,
#             }
#
#         return entities
#
#     ##################################################################
#     ##  build packages
#
#     def build_remote_entity_packages(self, reformed_req):
#         package = EntitiesPackage(self, self.remote_sys_code)
#         req_meta = reformed_req['meta']
#         if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
#             api_method = self.reformer.get_api_method(
#                 self.remote_sys_code,
#                 TambovEntityCode.REND_SERVICE,
#                 OperationCode.READ_ONE,
#             )
#             services_ids = self.get_services_ids(reformed_req)
#             self.set_services(services_ids, package, api_method, req_meta)
#         elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
#             api_method = self.reformer.get_api_method(
#                 self.remote_sys_code,
#                 TambovEntityCode.REND_SERVICE,
#                 OperationCode.READ_ONE,
#             )
#             self.set_services([req_meta['dst_id']], package, api_method, req_meta)
#         return package
#
#     def get_services_ids(self, reformed_req):
#         req = reformed_req
#         for param_name, param_data in req['meta']['dst_parents_params'].items():
#             req.data_update({param_name: param_data['id']})
#         res = self.transfer__send_request(req)
#         return res
#
#     def set_services(self, services_ids, package, api_method, req_meta):
#         for service_id in services_ids:
#             req = {
#                 'meta': {
#                     'dst_method': api_method['method'],
#                     'dst_url': api_method['template_url'],
#                 },
#                 'body': {
#                     'id': service_id,
#                 }
#             }
#             service_data = self.transfer__send_request(req)
#             main_item = package.add_main_pack_entity(
#                 entity_code=TambovEntityCode.REND_SERVICE,
#                 method=req['meta']['dst_method'],
#                 main_param_name='measure_id',
#                 main_id=service_id,
#                 parents_params=req_meta['dst_parents_params'],
#                 data=service_data,
#             )


    ##################################################################
    ##  build packages

    def build_local_entity_packages_exch_card(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()

        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        main_item = package.add_main_pack_entity(
            entity_code=RisarEntityCode.EXCHANGE_CARD,
            operation_code=msg_meta['src_operation_code'],
            method=msg_meta['dst_method'],
            main_param_name=msg_meta['src_main_param_name'],
            main_id=msg_meta['src_main_id'],
            parents_params=msg_meta['src_parents_params'],
            data=msg.get_data(),
        )

        return package


    ##################################################################
    ##  reform entities

    def build_remote_entities_exch_card(self, header_meta, pack_entity):
        exch_card_data = pack_entity['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid',
            },
            RisarEntityCode.ORGANIZATION: {
                'entity': TambovEntityCode.CLINIC, 'param': 'orgId',
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=TambovEntityCode.REND_SERVICE,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level_count=2,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                # 'id': None,  # проставляется в set_current_id_func
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'serviceId': '99999',
                # 'prototypeId': '11245',  # prototypeId не нужен, если заполнена услуга
                'isRendered': True,
                'orgId': header_meta['remote_parents_params']['orgId']['id'],
            }

        child_item = entities.set_child_entity(
            parent_item=main_item,
            dst_entity_code=TambovEntityCode.SRV_PROTOCOL,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name=None,
            dst_parent_id_name='id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
        )
        if src_operation_code != OperationCode.DELETE:
            child_item['body'] = exch_card_data['exch_card']

        return entities
