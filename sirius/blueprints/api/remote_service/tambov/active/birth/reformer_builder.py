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


class BirthTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.CARD: {
                'entity': TambovEntityCode.PATIENT, 'param': 'patientUid'
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

        birth_data = self.transfer__send_request(reformed_req)
        main_item = package.add_main_pack_entity(
            entity_code=TambovEntityCode.BIRTH,
            method=reformed_req.method,
            main_param_name='UID',
            main_id=birth_data['UID'],
            parents_params=req_meta['dst_parents_params'],
            data=birth_data,
        )
        return package

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        birth_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.PATIENT: {
                'entity': RisarEntityCode.CARD, 'param': 'card_id'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        main_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.CHILDBIRTH,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='card_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            part1 = birth_data['Part1']
            main_item['body'] = {
                'general_info': {
                    'admission_date': encode(part1['InDate']),
                    'pregnancy_duration': part1['PregnantTimeSpan']['Days'],
                    'delivery_date': encode(part1['ChildBirth']['Date']),
                    'delivery_time': encode(part1['ChildBirth']['Time']),
                    'maternity_hospital': part1['BornClinic'],
                    'maternity_hospital_doctor': part1['Employee'],
                    'diagnosis_osn': part1['Diagnoses']['Main'],
                    'pregnancy_final': part1['ChildBirthOutcome'],  # rbRisarPregnancy_Final
                },
                'kids': []
            }

        return entities
