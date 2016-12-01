#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.active.referral.srv_prototype_match import \
    SrvPrototypeMatch
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode

encode = WebMisJsonEncoder().default
to_date = lambda x: x and datetime.strptime(x, '%Y-%m-%d')


class ReferralTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        msg_meta['src_operation_code'] = self.get_operation_code_by_method(msg_meta['src_method'])
        if msg_meta['src_operation_code'] == OperationCode.READ_MANY:
            data = msg.get_data()
        elif msg_meta['src_operation_code'] == OperationCode.READ_ONE:
            data = [msg.get_data()]
        else:
            raise InternalError('Unexpected operation code')
        self.set_measures(data, package, msg_meta)
        return package

    def set_measures(self, measures, package, msg_meta):
        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_entity = msg_meta['src_entity_code']

        for measure_data in measures:
            measure_root = measure_item = package.add_main_pack_entity(
                entity_code=src_entity,
                operation_code=msg_meta['src_operation_code'],
                method=msg_meta['dst_method'],
                main_param_name='measure_id',
                main_id=measure_data['measure_id'],
                parents_params=msg_meta['src_parents_params'],
                data=measure_data,
            )

            data_req = DataRequest()
            data_req.set_meta(
                dst_system_code=SystemCode.LOCAL,
                dst_entity_code=RisarEntityCode.APPOINTMENT,
                dst_operation_code=OperationCode.READ_ONE,
                dst_id=measure_data['appointment_id'],
                dst_parents_params=msg_meta['src_parents_params'],
            )

            # self.reformer.set_local_id(data_req)
            self.reformer.set_request_service(data_req)
            appointment_data = self.reformer.local_request_by_req(data_req)
            appointment_item = package.add_addition_pack_entity(
                root_item=measure_root,
                parent_item=measure_item,
                entity_code=RisarEntityCode.APPOINTMENT,
                main_id=measure_data['appointment_id'],
                data=appointment_data,
            )

    ##################################################################
    ##  reform entities to remote

    def build_remote_entities(self, header_meta, pack_entity):
        """
        Вход в header_meta
        local_operation_code
        local_entity_code
        local_main_param_name
        local_main_id
        local_parents_params

        Выход в entity
        dst_entity_code
        dst_main_param_name
        """
        measure_data = pack_entity['data']
        appointment_node = pack_entity['addition'][RisarEntityCode.APPOINTMENT][0]
        appoint_data = appointment_node['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=TambovEntityCode.REFERRAL,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level_count=1,
        )
        prototype_id = SrvPrototypeMatch.get_prototype_id(measure_data.get('measure_type_code'))
        srv_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.SERVICE,
            OperationCode.READ_MANY,
        )
        req = DataRequest()
        req.set_req_params(
            url=srv_api_method['template_url'],
            method=srv_api_method['method'],
            data={
                'clinic': appoint_data.get('appointed_lpu'),
                'prototype': prototype_id,
            },
        )
        srvs_data = self.transfer__send_request(req)
        srv_data = srvs_data and srvs_data[0]  # считаем, что будет одна
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                # 'id': None,  # проставляется в set_current_id_func
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'referralDate': to_date(appoint_data.get('date')),
                'referralOrganizationId': appoint_data.get('appointed_lpu'),
                'refServiceId': srv_data.serviceId,
            }

        return entities


    ##################################################################
    ##  reform entities to local

    def build_local_entities(self, header_meta, pack_entity):
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']
        referral_data = pack_entity['data']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.SMART_PATIENT: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        measure_items = {}
        childs = pack_entity['childs']
        service_list = childs[TambovEntityCode.REND_SERVICE]
        for item in service_list:
            service_data = item['data']

            measure_type = SrvPrototypeMatch.get_measure_type(service_data.prototypeId)

            if measure_type in measure_items:
                measure_item = measure_items[header_meta['remote_main_id']]
            else:
                # todo: возможно передавать MEASURE не нужно
                measure_item = entities.set_main_entity(
                    dst_entity_code=RisarEntityCode.MEASURE,
                    dst_parents_params=header_meta['local_parents_params'],
                    dst_main_id_name='measure_id',
                    src_operation_code=src_operation_code,
                    src_entity_code=src_entity_code,
                    src_main_id_name=header_meta['remote_main_param_name'],
                    src_id=header_meta['remote_main_id'],
                    level_count=2,
                )
                measure_items[header_meta['remote_main_id']] = measure_item
                measure_id = SrvPrototypeMatch.get_measure_id(service_data.prototypeId)
                if src_operation_code != OperationCode.DELETE:
                    measure_item['body'] = {
                        # 'measure_id': None,  # заполняется в set_current_id_func
                        # пока считаем, что на одно направление
                        # не может быть разных measure_id из услуг
                        'measure_type_code': measure_id,
                        'begin_datetime': encode(referral_data['referralDate']),
                        'end_datetime': encode(referral_data['referralDate']),
                        'status': 'created',  # referral_data['refStatusId'],
                    }

            research_meas_types = ('lab_test', 'func_test')
            checkup_meas_types = ('checkup',)
            if measure_type in research_meas_types:
                self.build_local_measure_research(
                    header_meta, entities, service_data,
                    measure_item, measure_id
                )
            elif measure_type in checkup_meas_types:
                self.build_local_measure_specialists_checkup(
                    header_meta, entities, service_data,
                    measure_item, measure_id
                )
            else:
                # todo:
                raise NotImplementedError()
        return entities

    def build_local_measure_research(
        self, header_meta, entities, service_data, measure_item, measure_id
    ):
        src_operation_code = header_meta['remote_operation_code']

        research_item = entities.set_child_entity(
            parent_item=measure_item,
            dst_entity_code=RisarEntityCode.MEASURE_RESEARCH,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='result_action_id',
            dst_parent_id_name='measure_id',
            src_operation_code=src_operation_code,
            src_entity_code=TambovEntityCode.REND_SERVICE,
            src_main_id_name='id',
            src_id=service_data['id'],
        )
        if src_operation_code != OperationCode.DELETE:
            research_item['body'] = {
                # 'result_action_id': None,  # заполняется в set_current_id_func
                # 'measure_id':  # заполняется в set_parent_id_common_func
                'external_id': service_data['id'],
                'measure_type_code': measure_id,
                'realization_date': encode(service_data['dateFrom']),
                'lpu_code': safe_traverse(service_data, 'orgId', default=''),
                # 'analysis_number': service_data[''] or Undefined,
                'results': 'p1:1;p2:2',
                # 'comment': service_data[''] or Undefined,
                # 'doctor_code': service_data[''] or Undefined,
                # 'status': service_data[''] or Undefined,
            }

        return entities

    def build_local_measure_specialists_checkup(
        self, header_meta, entities, service_data, measure_item, measure_id
    ):
        src_operation_code = header_meta['remote_operation_code']

        research_item = entities.set_child_entity(
            parent_item=measure_item,
            dst_entity_code=RisarEntityCode.MEASURE_SPECIALISTS_CHECKUP,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='result_action_id',
            dst_parent_id_name='measure_id',
            src_operation_code=src_operation_code,
            src_entity_code=TambovEntityCode.REND_SERVICE,
            src_main_id_name='id',
            src_id=service_data['id'],
        )
        if src_operation_code != OperationCode.DELETE:
            research_item['body'] = {
                # 'result_action_id': None,  # заполняется в set_current_id_func
                # 'measure_id': None,  # заполняется в set_parent_id_common_func
                'external_id': service_data['id'],
                'measure_type_code': measure_id,
                'checkup_date': encode(service_data['dateTo']),
                'lpu_code': safe_traverse(service_data, 'orgId', default=''),
                'doctor_code': safe_traverse(service_data, 'resourceGroupId', default=''),
            }

        return entities
