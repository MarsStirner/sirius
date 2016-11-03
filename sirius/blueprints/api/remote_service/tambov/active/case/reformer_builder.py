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
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode

encode = WebMisJsonEncoder().default
to_date = lambda x: datetime.strptime(x, '%Y-%m-%d')


class CaseTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  build packages

    def build_local_entity_packages(self, msg):
        meta = msg.get_header().meta
        src_entity = meta['local_entity_code']
        checkup_code = None
        if src_entity == RisarEntityCode.CHECKUP_OBS_FIRST_TICKET:
            checkup_code = RisarEntityCode.CHECKUP_OBS_FIRST
        elif src_entity == RisarEntityCode.CHECKUP_OBS_SECOND_TICKET:
            checkup_code = RisarEntityCode.CHECKUP_OBS_SECOND
        ticket_code = src_entity

        entities = {}
        entity_packages = {
            'system_code': SystemCode.LOCAL,
            'entities': entities,
        }
        msg_meta = msg.get_relative_meta()
        self.set_tickets([msg.get_data()], entities, msg_meta, ticket_code, checkup_code)
        return entity_packages

    def set_tickets(self, tickets, entities, msg_meta, ticket_code, checkup_code):
        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_operation_code = self.get_operation_code_by_method(msg_meta['src_method'])

        for ticket_data in tickets:
            ticket_root_parent = ticket_node = {
                'is_changed': False,
                'operation_code': src_operation_code,
                'main_id': msg_meta['src_main_id'],
                'data': ticket_data,

                # 'method': msg_meta['dst_method'],
                'main_param_name': msg_meta['src_main_param_name'],
                'parents_params': msg_meta['src_parents_params'],
            }
            entities.setdefault(
                ticket_code, []
            ).append(ticket_node)

            req = {
                'meta': {
                    'src_parents_params': msg_meta['src_parents_params'],
                    'dst_entity_code': checkup_code,
                    'dst_operation_code': OperationCode.READ_ONE,
                    'dst_id_url_param_name': 'exam_obs_id',
                    'dst_id': msg_meta['src_main_id'],
                },
            }
            # self.reformer.set_local_id(req_data)
            self.reformer.set_request_service(req, SystemCode.LOCAL)
            ticket_addition = ticket_root_parent.setdefault('addition', {})
            checkup_data = self.reformer.local_request_by_req(req)
            checkup_node = {
                'main_id': msg_meta['src_main_id'],
                'data': checkup_data,
            }
            ticket_addition.setdefault(
                checkup_code, []
            ).append(checkup_node)

    ##################################################################
    ##  reform entities

    def build_remote_entities_first(self, header_meta, entity_package, addition_data):
        """
        Требует в header_meta
        local_operation_code
        local_entity_code
        local_main_param_name
        local_main_id
        local_parents_params

        Устанавливает в entity
        dst_entity_code
        """
        ticket_data = entity_package['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_parents_params(header_meta, src_entity_code, params_map)

        res = self.get_entity_node()
        main_item = self.set_main_entity(
            node=res,
            dst_entity_code=TambovEntityCode.CASE,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level=1,
            level_count=2,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                'id': Undefined,  # проставляется в set_current_id_func
                'uid': '2',
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'medicalOrganizationId': '1434663',
                'caseTypeId': '1',
                'initGoalId': '7',
                # 'careLevelId': ticket_data[''],
                # 'fundingSourceTypeId': ticket_data[''],
                # 'socialGroupId': ticket_data[''],
                # 'paymentMethodId': ticket_data[''],
                # 'careRegimenId': ticket_data[''],
            }

        for serv_code in ticket_data.get('medical_services', ()):
            item = self.set_child_entity(
                node=res,
                main_item=main_item,
                dst_entity_code=TambovEntityCode.SERVICE,
                dst_parents_params=header_meta['remote_parents_params'],
                dst_main_id_name='id',
                dst_parent_id_name='medicalCaseId',
                src_operation_code=src_operation_code,
                src_entity_code=src_entity_code,
                src_main_id_name=header_meta['local_main_param_name'],
                src_id=header_meta['local_main_id'],
                level=2,
                level_count=2,
            )
            if src_operation_code != OperationCode.DELETE:
                item['body'] = {
                    'id': Undefined,  # проставляется в set_current_id_func
                    'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                    # todo:
                    # 'serviceId': serv_code,  # из дозапроса к справочной системе
                }

        checkup_node = entity_package['addition'][RisarEntityCode.CHECKUP_OBS_FIRST][0]
        checkup_data = checkup_node['data']
        item = self.set_child_entity(
            node=res,
            main_item=main_item,
            dst_entity_code=TambovEntityCode.VISIT,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            dst_parent_id_name='caseId',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level=2,
            level_count=2,
        )
        if src_operation_code != OperationCode.DELETE:
            item['body'] = {
                'id': Undefined,  # проставляется в set_current_id_func
                'admissionDate': to_date(checkup_data['general_info']['date']),
                'goalId': '7',
                'placeId': '1',
                # 'reasonId': checkup_data['reason_code'],  # из дозапроса к справочной системе
            }

        # def set_parent_id(record):
        #     reform_meta = record['meta']
        #     parent_meta = reform_meta['parent_entity']['meta']
        #     reform_meta['dst_url'] = reform_meta['dst_url'].replace(
        #         parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
        #     )
        #     body = record['body']
        #     body['parent_id'] = parent_meta['meta']['dst_id']
        # for record in data['fetuses']:
        #     item = {
        #         'meta': {
        #             'src_entity_code': src_entity_code,
        #             'src_id': record['fetus_id'],
        #             'dst_entity_code': TambovEntityCode.CHECKUP_FETUS,
        #             'set_parent_id_func': set_parent_id,
        #             'parent_entity': main_item,
        #         },
        #     }
        #     res.setdefault(TambovEntityCode.CHECKUP_FETUS, []).append(item)
        #     if src_operation_code != OperationCode.DELETE:
        #         self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 2)
        #         item['body'] = {
        #             'code_1': record['code_1'],
        #             'code_2': addition_data['src_service_code']['code_2'],
        #         }
        #     else:
        #         self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 1)
        return res

    def build_remote_entities_second_copy1(self, header_meta, entity_package, addition_data):
        """
        Требует в header_meta
        local_operation_code
        local_entity_code
        local_main_param_name
        local_main_id
        local_parents_params

        Устанавливает в entity
        dst_entity_code
        """
        ticket_data = entity_package['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_parents_params(header_meta, src_entity_code, params_map)

        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'].update({
                'id': reform_meta['dst_id'],
            })

        res = self.get_entity_node()
        main_item = self.set_main_entity(
            node=res,
            dst_entity_code=TambovEntityCode.CASE,
            dst_parents_params=header_meta['remote_parents_params'],
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_id_url_param_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level=1,
            level_count=2,
            set_current_id_func=set_current_id_func,
        )
        if src_operation_code != OperationCode.DELETE:
            main_item['body'] = {
                'id': Undefined,  # проставляется в set_current_id_func
                # 'uid': ticket_data[''],
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                # 'medicalOrganizationId': ticket_data[''],
                # 'caseTypeId': ticket_data[''],
                # 'careLevelId': ticket_data[''],
                # 'fundingSourceTypeId': ticket_data[''],
                # 'socialGroupId': ticket_data[''],
                # 'paymentMethodId': ticket_data[''],
                # 'careRegimenId': ticket_data[''],
            }

        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'].update({
                'id': reform_meta['dst_id'],
            })
        def set_parent_id_func(record):
            reform_meta = record['meta']
            parent_meta = reform_meta['parent_entity']['meta']
            reform_meta['dst_url'] = reform_meta['dst_url'].replace(
                parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
            )
            record['body'] = {
                'medicalCaseId': parent_meta['meta']['dst_id'],
            }
        for serv_code in ticket_data.get('medical_services', ()):
            item = self.set_child_entity(
                node=res,
                main_item=main_item,
                dst_entity_code=TambovEntityCode.SERVICE,
                dst_parents_params=header_meta['remote_parents_params'],
                src_operation_code=src_operation_code,
                src_entity_code=src_entity_code,
                src_id_url_param_name=header_meta['local_main_param_name'],
                src_id=header_meta['local_main_id'],
                level=2,
                level_count=2,
                set_current_id_func=set_current_id_func,
                set_parent_id_func=set_parent_id_func,
            )
            if src_operation_code != OperationCode.DELETE:
                item['body'] = {
                    'id': Undefined,  # проставляется в set_current_id_func
                    'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                    # todo:
                    # 'serviceId': serv_code,  # из дозапроса к справочной системе
                }

        # todo:
        def set_current_id_func(record):
            reform_meta = record['meta']
            record['body'].update({
                'id': reform_meta['dst_id'],
            })
        def set_parent_id_func(record):
            reform_meta = record['meta']
            parent_meta = reform_meta['parent_entity']['meta']
            reform_meta['dst_url'] = reform_meta['dst_url'].replace(
                parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
            )
            record['body'] = {
                'caseId': parent_meta['meta']['dst_id'],
            }
        checkup_node = entity_package['addition'][RisarEntityCode.CHECKUP_OBS_SECOND][0]
        checkup_data = checkup_node['data']
        item = self.set_child_entity(
            node=res,
            main_item=main_item,
            dst_entity_code=TambovEntityCode.VISIT,
            dst_parents_params=header_meta['remote_parents_params'],
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_id_url_param_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
            level=2,
            level_count=2,
            set_current_id_func=set_current_id_func,
            set_parent_id_func=set_parent_id_func,
        )
        if src_operation_code != OperationCode.DELETE:
            item['body'] = {
                'id': Undefined,  # проставляется в set_current_id_func
                # 'reasonId': checkup_data['reason_code'],  # из дозапроса к справочной системе
            }

        # def set_parent_id(record):
        #     reform_meta = record['meta']
        #     parent_meta = reform_meta['parent_entity']['meta']
        #     reform_meta['dst_url'] = reform_meta['dst_url'].replace(
        #         parent_meta['dst_id_url_param_name'], parent_meta['dst_id']
        #     )
        #     record['body'] = {
        #         'parent_id': parent_meta['meta']['dst_id'],
        #     }
        #
        # for record in data['fetuses']:
        #     item = {
        #         'meta': {
        #             'src_entity_code': src_entity_code,
        #             'src_id': record['fetus_id'],
        #             'dst_entity_code': TambovEntityCode.CHECKUP_FETUS,
        #             'set_parent_id_func': set_parent_id,
        #             'parent_entity': main_item,
        #         },
        #     }
        #     res.setdefault(TambovEntityCode.CHECKUP_FETUS, []).append(item)
        #     if src_operation_code != OperationCode.DELETE:
        #         self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 2)
        #         item['body'] = {
        #             'code_1': record['code_1'],
        #             'code_2': addition_data['src_service_code']['code_2'],
        #         }
        #     else:
        #         self.set_operation_order(res, TambovEntityCode.CHECKUP_FETUS, 1)
        return res
