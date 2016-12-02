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
            hospital_rec_ids = self.get_hospital_rec_ids(reformed_req)
            self.set_hospitals(hospital_rec_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_hospitals([req_meta['dst_id']], package, req_meta)
        return package

    def get_hospital_rec_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({param_name: param_data['id']})
        res = self.transfer__send_request(req)
        return res

    def set_hospitals(self, hospital_rec_ids, package, req_meta):

        for hospital_rec_id in hospital_rec_ids:
            main_hosp_item, hospital_rec_data = package.add_main(
                entity_code=TambovEntityCode.HOSPITAL_REC,
                main_id_name='id',
                main_id=hospital_rec_id,
                parents_params=req_meta['dst_parents_params'],
            )

            package.add_addition(
                parent_item=main_hosp_item,
                entity_code=TambovEntityCode.CASE,
                main_id_name='id',
                main_id=hospital_rec_data['caseId'],
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
            hosp_entity['body'] = {
                # 'result_action_id': None,  # заполняется в set_current_id_func
                # 'measure_id': None,  # мис сама не отдаёт направление госп.
                'hospital': case_data['medicalOrganizationId'],
                'doctor': hospital_rec_data['resourceGroupId'],
                'diagnosis_in': 'A01.1',  # нет поля в сервисе, они будут доделывать
                'diagnosis_out': 'A01.1',  # нет поля в сервисе, они будут доделывать
                # --
                'external_id': header_meta['remote_main_id'],
                'date_in': encode(hospital_rec_data['admissionDate']),
                'date_out': encode(hospital_rec_data['outcomeDate']),
            }
        return entities
