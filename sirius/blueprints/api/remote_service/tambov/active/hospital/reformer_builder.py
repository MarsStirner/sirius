#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime, timedelta

from hitsl_utils.safe import safe_traverse, safe_int, safe_traverse_attrs
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.api.remote_service.tambov.lib.diags_match import \
    DiagsMatch
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
to_date = lambda x: x and datetime.strptime(x, '%Y-%m-%d')


class HospitalTambovBuilder(Builder):
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
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            # пока без удаления
            # package.enable_diff_check()
            # package.set_diff_key_range()
            hospital_rec_ids = self.get_hospital_rec_ids(reformed_req)
            self.set_hospitals(hospital_rec_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_hospitals([req_meta['dst_id']], package, req_meta)
        return package

    def get_hospital_rec_ids(self, reformed_req):
        req = reformed_req
        last_request_datetime = SchGrReqExecute.last_datetime(
            RisarEntityCode.MEASURE_HOSPITALIZATION
        ) or datetime.today()
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({
                param_name: param_data['id'],
                'closedFromDate': last_request_datetime.date() - timedelta(1),
            })
        res = self.transfer__send_request(req)
        return res

    def set_hospitals(self, hospital_rec_ids, package, req_meta):

        hosp_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.HOSPITAL_REC,
            OperationCode.READ_ONE,
        )

        hosp_recs_by_case = {}
        for hospital_rec_id in hospital_rec_ids:
            req = DataRequest()
            req.set_req_params(
                url=hosp_api_method['template_url'],
                method=hosp_api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={'id': hospital_rec_id},
            )
            hospital_rec_data = self.transfer__send_request(req)
            hosp_recs_by_case.setdefault(hospital_rec_data['caseId'], {}).update(
                {int(hospital_rec_id): hospital_rec_data}
            )

        for hosp_rec_case_id, hosp_recs_dict in hosp_recs_by_case.iteritems():
            earliest_hosp_rec = hosp_recs_dict[min(hosp_recs_dict)]
            latest_hosp_rec = hosp_recs_dict[max(hosp_recs_dict)]

            main_hosp_item = package.add_main_pack_entity(
                entity_code=TambovEntityCode.HOSPITAL_REC,
                method=hosp_api_method['method'],
                main_param_name='caseId',
                main_id=hosp_rec_case_id,
                parents_params=req_meta['dst_parents_params'],
                data={
                    'resourceGroupId': latest_hosp_rec['resourceGroupId'],
                    'admissionDate': earliest_hosp_rec['admissionDate'],
                    'outcomeDate': latest_hosp_rec['outcomeDate'],
                },
                # diff_key=diff_key,
            )

            package.add_addition(
                parent_item=main_hosp_item,
                entity_code=TambovEntityCode.CASE,
                main_id_name='id',
                main_id=hosp_rec_case_id,
            )


    ##################################################################
    ##  reform entities to local

    def build_local_entities(self, header_meta, pack_entity):
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']
        hospital_rec_data = pack_entity['data']
        case_entity = pack_entity['addition'][TambovEntityCode.CASE][0]
        case_data = case_entity['data']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.SMART_PATIENT: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)
        dm = DiagsMatch()

        entities = RequestEntities()
        hosp_entity = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.MEASURE_HOSPITALIZATION,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='result_action_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            employee_position_id = self.get_employee_position(hospital_rec_data['resourceGroupId'])
            diag_1_code = diag_4_code = None
            for diag_data in case_data['diagnoses']:
                if diag_data['stageId'] == '1':
                    diag_1_code = dm.diag_code(diag_data['diagnosId'])
                elif diag_data['stageId'] == '4':
                    diag_4_code = dm.diag_code(diag_data['diagnosId'])
            hosp_entity['body'] = {
                # 'result_action_id': None,  # заполняется в set_current_id_func
                # 'measure_id': None,  # мис сама не отдаёт направление госп.
                'hospital': case_data['medicalOrganizationId'],
                'doctor': employee_position_id,
                'diagnosis_in': diag_1_code or 'A01.1',  # нет поля в сервисе, они будут доделывать
                'diagnosis_out': diag_4_code or 'A01.1',  # нет поля в сервисе, они будут доделывать
                # --
                'external_id': header_meta['remote_main_id'],
                'date_in': encode(hospital_rec_data['admissionDate']) or Undefined,
                'date_out': encode(hospital_rec_data['outcomeDate']) or Undefined,
                'status': 'performed',
            }
        return entities

    def get_employee_position(self, location_id):
        location_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.LOCATION,
            OperationCode.READ_ONE,
        )
        req = DataRequest()
        req.set_req_params(
            url=location_api_method['template_url'],
            method=location_api_method['method'],
            protocol=ProtocolCode.SOAP,
            data={'location': location_id},
        )
        location_data = self.transfer__send_request(req)

        res = None
        for employeePosition_item in safe_traverse_attrs(
                location_data, 'employeePositionList', 'EmployeePosition'
        ) or []:
            if not self.valid_employee_position(employeePosition_item):
                continue
            res = employeePosition_item['employeePosition']
            # валидный врач должен быть в ресурсе только один
            break
        return res

    def valid_employee_position(self, employeePosition_item):
        if not employeePosition_item['resourceRole'] == '1':
            return False
        doctor_id = self.reformer.find_local_id_by_remote(
            RisarEntityCode.DOCTOR,
            TambovEntityCode.EMPLOYEE_POSITION,
            employeePosition_item['employeePosition'],
        )
        if not doctor_id:
            return False
        return True
