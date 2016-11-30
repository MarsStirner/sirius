#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from safe import safe_date

from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
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

        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        self.set_tickets([msg.get_data()], package, msg_meta, ticket_code, checkup_code)
        return package

    def set_tickets(self, tickets, package, msg_meta, ticket_code, checkup_code):
        # дополнение параметров сущностью, если не указана
        params_meta = {'card_id': RisarEntityCode.CARD}
        self.set_src_parents_entity(msg_meta, params_meta)

        src_operation_code = self.get_operation_code_by_method(msg_meta['src_method'])

        for ticket_data in tickets:
            root_item = main_item = package.add_main_pack_entity(
                entity_code=ticket_code,
                operation_code=src_operation_code,
                method=msg_meta['dst_method'],
                main_param_name=msg_meta['src_main_param_name'],
                main_id=msg_meta['src_main_id'],
                parents_params=msg_meta['src_parents_params'],
                data=ticket_data,
            )

            data_req = DataRequest()
            data_req.set_meta(
                dst_system_code=SystemCode.LOCAL,
                dst_entity_code=checkup_code,
                dst_operation_code=OperationCode.READ_ONE,
                dst_id=msg_meta['src_main_id'],
                dst_parents_params=msg_meta['src_parents_params'],
            )

            # self.reformer.set_local_id(data_req)
            self.reformer.set_request_service(data_req)
            checkup_data = self.reformer.local_request_by_req(data_req)
            package.add_addition_pack_entity(
                root_item=root_item,
                parent_item=main_item,
                entity_code=checkup_code,
                main_id=msg_meta['src_main_id'],
                data=checkup_data,
            )

    ##################################################################
    ##  reform entities

    def build_remote_entities_first(self, header_meta, pack_entity):
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
        ticket_data = pack_entity['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=TambovEntityCode.CASE,
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
                'uid': str(header_meta['local_main_id']),
                'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                'medicalOrganizationId': safe_traverse(ticket_data, 'hospital', default=''),
                'caseTypeId': '1',
                'initGoalId': safe_traverse(ticket_data, 'visit_type', default=''),
                # 'careLevelId': ticket_data[''],
                'fundingSourceTypeId': '1',
                # 'socialGroupId': ticket_data[''],
                # 'paymentMethodId': ticket_data[''],
                'careRegimenId': '1',
                'establishmentDate': to_date(safe_traverse(ticket_data, 'date_open')),
            }

        for serv_code in safe_traverse(ticket_data, 'medical_services', default=()):
            item = entities.set_child_entity(
                parent_item=main_item,
                dst_entity_code=TambovEntityCode.SERVICE,
                dst_parents_params=header_meta['remote_parents_params'],
                dst_main_id_name='id',
                dst_parent_id_name='medicalCaseId',
                src_operation_code=src_operation_code,
                src_entity_code=src_entity_code,
                src_main_id_name=header_meta['local_main_param_name'],
                src_id=header_meta['local_main_id'],
            )
            if src_operation_code != OperationCode.DELETE:
                item['body'] = {
                    # 'id': None,  # проставляется в set_current_id_func
                    'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                    'serviceId': safe_traverse(serv_code, 'medical_service', default=''),
                    'dateFrom': to_date(safe_traverse(ticket_data, 'date_open')),
                    'isRendered': True,
                    'orgId': safe_traverse(ticket_data, 'hospital', default=''),
                }

        checkup_node = pack_entity['addition'][RisarEntityCode.CHECKUP_OBS_FIRST][0]
        checkup_data = checkup_node['data']
        item = entities.set_child_entity(
            parent_item=main_item,
            dst_entity_code=TambovEntityCode.VISIT,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='id',
            dst_parent_id_name='caseId',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            src_id=header_meta['local_main_id'],
        )
        if src_operation_code != OperationCode.DELETE:
            item['body'] = {
                # 'id': None,  # проставляется в set_current_id_func
                'admissionDate': to_date(checkup_data['general_info']['date']),
                'goalId': '7',
                'placeId': '1',
                'diagnosId': safe_traverse(ticket_data, 'medical_report', 'diagnosis_osn', default=''),
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
        return entities
