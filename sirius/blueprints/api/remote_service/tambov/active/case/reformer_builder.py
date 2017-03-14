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
from sirius.blueprints.api.remote_service.tambov.lib.diags_match import \
    DiagsMatch
from sirius.blueprints.monitor.exception import InternalError, ExternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.models.operation import OperationCode
from sirius.models.protocol import ProtocolCode
from sirius.models.system import SystemCode

encode = lambda x: x and WebMisJsonEncoder().default(x)
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
            if not self.validate_ticket(ticket_data):
                continue
            data_req = DataRequest(self.reformer.stream_id)
            data_req.set_meta(
                dst_system_code=SystemCode.LOCAL,
                dst_entity_code=checkup_code,
                dst_operation_code=OperationCode.READ_ONE,
                dst_id=msg_meta['src_main_id'],
                dst_parents_params=msg_meta['src_parents_params'],
            )
            data_req.req_data['meta']['dst_id_url_param_name'] = 'exam_obs_id'

            # self.reformer.set_local_id(data_req)
            self.reformer.set_request_service(data_req)
            checkup_data = self.reformer.local_request_by_req(data_req)

            if not self.validate_checkup(checkup_data, checkup_code):
                continue

            root_item = main_item = package.add_main_pack_entity(
                entity_code=ticket_code,
                operation_code=src_operation_code,
                method=msg_meta['dst_method'],
                main_param_name=msg_meta['src_main_param_name'],
                main_id=msg_meta['src_main_id'],
                parents_params=msg_meta['src_parents_params'],
                data=ticket_data,
            )

            package.add_addition_pack_entity(
                root_item=root_item,
                parent_item=main_item,
                entity_code=checkup_code,
                main_id=msg_meta['src_main_id'],
                data=checkup_data,
            )

    def validate_ticket(self, ticket_data):
        values = (
            safe_traverse(ticket_data, 'diagnosis'),
            to_date(safe_traverse(ticket_data, 'date_open')),
            safe_traverse(ticket_data, 'visit_type'),
            safe_traverse(ticket_data, 'disease_character'),
            safe_traverse(ticket_data, 'disease_outcome'),
            safe_traverse(ticket_data, 'treatment_result'),
            safe_traverse(ticket_data, 'medical_care'),
            # safe_traverse(ticket_data, 'medical_care_emergency'),
            safe_traverse(ticket_data, 'medical_care_profile'),
            any(map(
                self.validate_service,
                (safe_traverse(ticket_data, 'medical_services') or ())
            )),
        )
        return all(values)

    @staticmethod
    def validate_service(service_data):
        values = (
            safe_traverse(service_data, 'medical_service'),
            safe_traverse(service_data, 'medical_service_quantity'),
            safe_traverse(service_data, 'medical_service_doctor'),
        )
        return all(values)

    @staticmethod
    def validate_checkup(checkup_data, checkup_code):
        if checkup_code == RisarEntityCode.CHECKUP_OBS_FIRST:
            gen_info = 'general_info'
        else:
            gen_info = 'dynamic_monitoring'
        values = (
            safe_traverse(checkup_data, 'medical_report', 'diagnosis_osn', 'MKB'),
            to_date(safe_traverse(checkup_data[gen_info], 'date')),
        )
        return all(values)

    ##################################################################
    ##  reform entities

    def build_remote_entities_first(self, header_meta, pack_entity):
        gen_info = 'general_info'
        checkup_code = RisarEntityCode.CHECKUP_OBS_FIRST
        return self.build_remote_entities_checkup(header_meta, pack_entity,
                                                  checkup_code, gen_info)

    def build_remote_entities_second(self, header_meta, pack_entity):
        gen_info = 'dynamic_monitoring'
        checkup_code = RisarEntityCode.CHECKUP_OBS_SECOND
        return self.build_remote_entities_checkup(header_meta, pack_entity,
                                                  checkup_code, gen_info)

    def build_remote_entities_checkup(self, header_meta, pack_entity, checkup_code, gen_info):
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
        resource_group_id = None

        # сопоставление параметров родительских сущностей
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid'
            }
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)
        dm = DiagsMatch()

        entities = RequestEntities(self.reformer.stream_id)
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
                'medicalOrganizationId': safe_traverse(ticket_data, 'hospital') or '',
                'caseTypeId': '1',
                'fundingSourceTypeId': '1',
                'careRegimenId': '1',
                'paymentMethodId': '22',
                'careLevelId': safe_traverse(ticket_data, 'medical_care'),
                # неотложная или плановая
                'careProvidingFormId': 2 if safe_traverse(ticket_data, 'medical_care_emergency') else 3,
                'initGoalId': safe_traverse(ticket_data, 'visit_type') or '7',
                'stateId': '1',
            }
            diagnosis = safe_traverse(ticket_data, 'diagnosis')
            if diagnosis:
                main_item['body']['diagnoses'] = [{
                    'stageId': 3,
                    'main': True,
                    'diagnosId': dm.safe_diag_id(diagnosis),
                    'establishmentDate': to_date(safe_traverse(ticket_data, 'date_open')),
                    'diseaseTypeId': safe_traverse(ticket_data, 'disease_character'),
                }]

        checkup_node = pack_entity['addition'][checkup_code][0]
        checkup_data = checkup_node['data']
        visit_item = entities.set_child_entity(
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
            visit_item['body'] = {
                # 'id': None,  # проставляется в set_current_id_func
                'visitResultId': safe_traverse(ticket_data, 'treatment_result'),
                'deseaseResultId': safe_traverse(ticket_data, 'disease_outcome'),
                'admissionDate': to_date(safe_traverse(checkup_data[gen_info], 'date')),
                'goalId': safe_traverse(ticket_data, 'visit_type') or '7',
                'placeId': '1',
                'profileId': safe_traverse(ticket_data, 'medical_care_profile'),
            }
            if not self.reformer.find_remote_id_by_local(
                TambovEntityCode.VISIT,
                src_entity_code,
                header_meta['local_main_id'],
            ):
                resource_group_id = self.get_resource_group_id(ticket_data['hospital'], ticket_data['doctor'])
                visit_item['body']['resourceGroupId'] = resource_group_id
            diagnosis_osn = safe_traverse(checkup_data, 'medical_report', 'diagnosis_osn', 'MKB')
            if diagnosis_osn:
                diags_osl = safe_traverse(checkup_data, 'medical_report', 'diagnosis_osl')
                diags_sop = safe_traverse(checkup_data, 'medical_report', 'diagnosis_sop')
                visit_diagnoses = visit_item['body'].setdefault('diagnoses', [])
                gen_info_date = to_date(safe_traverse(checkup_data[gen_info], 'date'))
                disease_character = safe_traverse(ticket_data, 'disease_character')
                self.add_visit_diagnosis(
                    visit_diagnoses,
                    diagnosis_osn,
                    '1',
                    gen_info_date,
                    disease_character,
                    dm
                )
                for diagnosis_osl in diags_osl or ():
                    self.add_visit_diagnosis(
                        visit_diagnoses,
                        safe_traverse(diagnosis_osl, 'MKB'),
                        '3',
                        gen_info_date,
                        disease_character,
                        dm
                    )
                for diagnosis_sop in diags_sop or ():
                    self.add_visit_diagnosis(
                        visit_diagnoses,
                        safe_traverse(diagnosis_sop, 'MKB'),
                        '2',
                        gen_info_date,
                        disease_character,
                        dm
                    )

        srv_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.SERVICE,
            OperationCode.READ_MANY,
        )
        for medical_serv_item in (safe_traverse(ticket_data, 'medical_services') or ()):
            if not self.validate_service(medical_serv_item):
                continue
            prototype_code = safe_traverse(medical_serv_item, 'medical_service') or ''
            prototype_id = SrvPrototypeMatch.get_prototype_id_by_prototype_code(prototype_code)

            def set_parent_id_func(parent_meta, entity_meta, entity_body):
                case_meta = parent_meta['parent_entity']['meta']
                entity_body['medicalCaseId'] = case_meta['dst_id']
            serv_item = entities.set_child_entity(
                parent_item=visit_item,
                dst_entity_code=TambovEntityCode.REND_SERVICE,
                dst_parents_params=header_meta['remote_parents_params'],
                dst_main_id_name='id',
                dst_parent_id_name='stepId',
                src_operation_code=src_operation_code,
                src_entity_code=src_entity_code,
                src_main_id_name=header_meta['local_main_param_name'],
                src_id='_'.join((str(header_meta['local_main_id']), prototype_id)),
                set_parent_id_func=set_parent_id_func,
            )
            org_code = safe_traverse(ticket_data, 'hospital') or ''
            req = DataRequest(self.reformer.stream_id)
            req.set_req_params(
                url=srv_api_method['template_url'],
                method=srv_api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={
                    'clinic': org_code,
                    'prototype': prototype_id,
                },
            )
            srvs_data = self.transfer__send_request(req)
            if not srvs_data:
                raise ExternalError('%s not found for clinic="%s" prototype="%s"' % (
                    TambovEntityCode.SERVICE, org_code, prototype_id
                ))
            srv_data = srvs_data[0]  # считаем, что будет одна
            if src_operation_code != OperationCode.DELETE:
                serv_item['body'] = {
                    # 'id': None,  # проставляется в set_current_id_func
                    'patientUid': header_meta['remote_parents_params']['patientUid']['id'],
                    'serviceId': srv_data['id'],
                    'dateFrom': to_date(safe_traverse(ticket_data, 'date_open')),
                    'dateTo': to_date(safe_traverse(ticket_data, 'date_open')),
                    'isRendered': True,
                    'orgId': safe_traverse(ticket_data, 'hospital') or '',
                    'quantity': safe_traverse(medical_serv_item, 'medical_service_quantity'),
                    'fundingSourceTypeId': 1,
                }
                diagnosis = safe_traverse(ticket_data, 'diagnosis')
                if diagnosis:
                    serv_item['body']['diagnosisId'] = dm.diag_id(diagnosis)
                if not self.reformer.find_remote_id_by_local(
                        TambovEntityCode.REND_SERVICE,
                        src_entity_code,
                        '_'.join((str(header_meta['local_main_id']), prototype_id)),
                ):
                    resource_group_id = self.get_resource_group_id(
                        ticket_data['hospital'],
                        safe_traverse(medical_serv_item, 'medical_service_doctor')
                    )
                    serv_item['body']['resourceGroupId'] = resource_group_id

        return entities

    def get_resource_group_id(self, clinic_id, empl_position_id):
        location_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.LOCATION,
            OperationCode.ADD,
        )
        req = DataRequest(self.reformer.stream_id)
        req.set_req_params(
            url=location_api_method['template_url'],
            method=location_api_method['method'],
            protocol=ProtocolCode.SOAP,
            data={
                'location': {
                    'organization': clinic_id,
                    'system': True,
                    'employeePositionList': {
                        'EmployeePosition': [{
                            'resourceRole': 1,
                            'employeePosition': empl_position_id,
                        }]
                    }
                },
            },
        )
        location_id = self.transfer__send_request(req)
        return location_id

    def add_visit_diagnosis(self, diagnoses, diagnosis, typeId, gen_info_date, disease_character, dm):
        diagnoses.append({
            'stageId': '4',
            'typeId': typeId,
            'main': typeId == '1',
            'diagnosId': dm.safe_diag_id(diagnosis),
            'establishmentDate': gen_info_date,
            'diseaseTypeId': disease_character,
        })
