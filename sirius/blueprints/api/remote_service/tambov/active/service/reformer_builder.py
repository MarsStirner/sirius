#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
import logging
from datetime import date, datetime, timedelta

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.lib.transfer import \
    RequestModeCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import ExternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.blueprints.scheduler.models import SchGrReqExecute
from sirius.models.protocol import ProtocolCode
from sirius.models.system import SystemCode
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode

encode = lambda x: x and WebMisJsonEncoder().default(x)
to_date = lambda x: datetime.strptime(x, '%Y-%m-%d')
logger = logging.getLogger('simple')


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
            # todo: переопределить diff_key. (в ответе должен быть dateFrom)
            # отключено: если мис исправит баг по dateFrom, то на одни и те же услуги будут разные ключи
            # package.enable_diff_check()
            services_ids = self.get_services_ids(reformed_req, package)
            self.set_services(services_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_services([req_meta['dst_id']], package, req_meta)
        return package

    def get_services_ids(self, reformed_req, package):
        req = reformed_req
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({
                param_name: param_data['id'],
                # 'medicalOrganizationId': '89',  # todo: для тестов
            })

        last_request_datetime = SchGrReqExecute.last_datetime(
            RisarEntityCode.MEASURE_RESEARCH
        )
        cur_datetime = datetime.today()
        req_date = (last_request_datetime or cur_datetime).date() - timedelta(1)
        package.set_diff_key_range((req_date.isoformat(),
                                    cur_datetime.date().isoformat()))
        # в мис баг. dateFrom не диапазон, а дата. обходим.
        '''
        searchServiceRend
        <typ:patientUid>ITPEJZ6JOK9S8EQ2</typ:patientUid>
        <typ:dateFrom>2017-01-17</typ:dateFrom>
        если выдает пустоту, значит в мис не исправили баг еще
        '''
        ids_set = set()
        while req_date <= cur_datetime.date():
            # diff_key = req_date.isoformat()
            req.data_update({'dateFrom': req_date})
            res = self.transfer__send_request(req)
            ids_set.update(res)
            # ids_set.update(((r, diff_key) for r in res))
            req_date += timedelta(1)
        return ids_set

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

        referralIds = set()
        # for rend_service_id, diff_key in rend_services_ids:
        for rend_service_id in rend_services_ids:
            req = DataRequest(self.reformer.stream_id)
            req.set_req_params(
                url=rend_serv_api_method['template_url'],
                method=rend_serv_api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={'id': rend_service_id},
            )
            rend_service_data = self.transfer__send_request(req)
            # без прототипа не поймем каким методом отправлять
            srv_api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_ONE,
            )
            req = DataRequest(self.reformer.stream_id)
            req.set_req_params(
                url=srv_api_method['template_url'],
                method=srv_api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={
                    'serviceId': rend_service_data['serviceId'],
                },
            )
            srv_data = self.transfer__send_request(req)
            prototypeId = srv_data['prototype']
            rend_service_data['prototypeId'] = prototypeId
            if not prototypeId:
                # большинство услуг с разных мо без прототипа
                # logger.error(
                #     "stream_id: %s Missing required prototypeId in referralId = '%s'. rend_service_id = '%s'" %
                #     (self.reformer.stream_id, rend_service_data['referralId'], rend_service_data['id'])
                # )
                continue

            # на одно направление должна быть только одна услуга.
            # остальные откидываем
            referralId = rend_service_data['referralId']
            if referralId and referralId in referralIds:
                logger.error(
                    'stream_id: %s referralId "%s" already have other rend_service_id. Skipped current rend_service_id = "%s"' %
                    (self.reformer.stream_id, referralId, rend_service_id)
                )
                continue
            referralIds.add(referralId)
            # если есть направление - отправляем его и услугу.
            # если нет направления - отправляем только услугу.
            # обратная передача, автоматом созданного направления в МР, уйдет
            # в МИС и будет висеть там, даже, если уже там назначили
            # направление на услугу.
            # если в мис проставят другое направление, то в МР по-хорошему
            # должны создать новое и перепривязать услугу.
            if referralId:
                req = DataRequest(self.reformer.stream_id)
                req.set_req_params(
                    url=referral_api_method['template_url'],
                    method=referral_api_method['method'],
                    protocol=ProtocolCode.SOAP,
                    data={'id': referralId},
                )
                referral_data = self.transfer__send_request(req)
            else:
                # так как в мис направление не указано, а изменения по
                # направлению нужно засечь и код не хотим дублировать в услугах
                # и навлениях, то обозначим направление мис фейковым ID, но с
                # пустыми данными, что бы в итоге направление не писать в МР
                referralId = '_'.join(('rend_serviceId', rend_service_id))
                referral_data = {}

            main_item = package.add_main_pack_entity(
                entity_code=TambovEntityCode.REFERRAL,
                method=req.method,
                main_param_name='id',
                main_id=referralId,
                parents_params=req_meta['dst_parents_params'],
                data=referral_data,
                # diff_key=diff_key,
            )

            rend_srv_item = package.add_child_pack_entity(
                root_item=main_item,
                parent_item=main_item,
                entity_code=TambovEntityCode.REND_SERVICE,
                method=req.method,
                main_id=rend_service_id,
                data=rend_service_data,
                # diff_key=diff_key,
            )

            # data_req = DataRequest(self.reformer.stream_id)
            # data_req.set_meta(
            #     dst_system_code=self.remote_sys_code,
            #     dst_entity_code=TambovEntityCode.DATA_REND_SERVICE,
            #     dst_operation_code=OperationCode.READ_ONE,
            #     dst_id=rend_service_id,
            #     dst_parents_params=req_meta['dst_parents_params'],
            #     dst_id_url_param_name='main_id',
            # )
            # # self.reformer.set_local_id(data_req)
            # self.reformer.set_request_service(data_req)
            # data_rend_srv_data = self.transfer__send_request(data_req)
            # data_rend_srv_item = package.add_addition_pack_entity(
            #     root_item=main_item,
            #     parent_item=rend_srv_item,
            #     entity_code=TambovEntityCode.DATA_REND_SERVICE,
            #     main_id=rend_service_id,
            #     data=data_rend_srv_data,
            # )
            data_req = DataRequest(self.reformer.stream_id)
            data_req.set_meta(
                dst_system_code=self.remote_sys_code,
                dst_entity_code=TambovEntityCode.SERVICE_ATTACHMENT,
                dst_operation_code=OperationCode.READ_MANY,
                dst_id=None,
                dst_parents_params={'rend_serv': {'id': rend_service_id,
                                                  'entity': TambovEntityCode.REND_SERVICE}},
                dst_id_url_param_name='main_id',
            )
            # self.reformer.set_local_id(data_req)
            self.reformer.set_request_service(data_req)
            srv_attachment_data = self.transfer__send_request(data_req)
            package.add_addition_pack_entity(
                root_item=main_item,
                parent_item=rend_srv_item,
                entity_code=TambovEntityCode.SERVICE_ATTACHMENT,
                main_id=rend_service_id,
                data=srv_attachment_data,
                # diff_key=diff_key,
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
#         entities = RequestEntities(self.reformer.stream_id)
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

        # отфильтруется из-за второго поста
        # protocol_id = self.reformer.find_remote_id_by_local(
        #     TambovEntityCode.SRV_PROTOCOL,
        #     RisarEntityCode.EXCHANGE_CARD,
        #     msg_meta['src_main_id'],
        # )
        # карту уже передавали
        # if protocol_id:
        #     return package

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

        entities = RequestEntities(self.reformer.stream_id)
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
            clinic_id = header_meta['remote_parents_params']['orgId']['id']
            srv_api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.SERVICE,
                OperationCode.READ_MANY,
            )
            req = DataRequest(self.reformer.stream_id)
            req.set_req_params(
                url=srv_api_method['template_url'],
                method=srv_api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={
                    'clinic': clinic_id,
                    'prototype': '11245',
                    'code': '99999',
                },
            )
            srvs_data = self.transfer__send_request(req)
            if not srvs_data:
                raise ExternalError('%s not found for clinic="%s" prototype="%s" code="%s"' % (
                    TambovEntityCode.SERVICE,
                    clinic_id, '11245', '99999'
                ))
            srv_data = srvs_data[0]  # считаем, что будет одна
            today = datetime.today()

            main_item['body'] = {
                # 'id': None,  # проставляется в set_current_id_func
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'serviceId': srv_data['id'],
                'isRendered': True,
                'orgId': clinic_id,
                'dateFrom': today,
                'dateTo': today,
            }

        child_item = entities.set_child_entity(
            parent_item=main_item,
            dst_entity_code=TambovEntityCode.SRV_PROTOCOL,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            dst_parent_id_name='id',
            dst_request_mode=RequestModeCode.MULTIPART_FILE,
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
        )
        if src_operation_code != OperationCode.DELETE:
            child_item['body'] = {
                'exch_card_1.xml': exch_card_data['exch_card'].replace('\n', '')
            }

        return entities
