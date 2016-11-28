#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date

from hitsl_utils.safe import safe_traverse_attrs, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = WebMisJsonEncoder().default


class ClinicTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

    ##################################################################
    ##  build packages by req

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            req = reformed_req.copy()
            clinics_ids = self.transfer__send_request(req)
            self.set_clinics(clinics_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_clinics([req_meta['dst_id']], package, req_meta)
        else:
            raise InternalError('Unexpected dst_operation_code')
        return package

    def set_clinics(self, clinics, package, req_meta):
        for clinic_id in clinics[:7]:
            clinic_item, clinic_data = package.add_main(
                entity_code=TambovEntityCode.CLINIC,
                main_id_name='clinic',
                main_id=clinic_id,
                parents_params=req_meta['dst_parents_params'],
            )

            AddressAllInfo_data = package.add_addition(
                parent_item=clinic_item,
                entity_code=TambovEntityCode.ADDRESS_ALL_INFO,
                main_id_name='id',
                main_id=safe_traverse_attrs(clinic_data, 'actualAddress', 'addressId'),
            )

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        clinic_data = pack_entity['data']
        clinic_addition = pack_entity.get('addition', {})
        AddressAllInfos = clinic_addition.get(TambovEntityCode.ADDRESS_ALL_INFO)
        entities = RequestEntities()

        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        # params_map = {
        #     TambovEntityCode.PATIENT: {
        #         'entity': RisarEntityCode.CARD, 'param': 'card_id'
        #     }
        # }
        # self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        org_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.ORGANIZATION,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='TFOMSCode',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            self.build_local_org_body(org_item, clinic_data, AddressAllInfos, header_meta)

        return entities

    def build_local_org_body(self, org_item, clinic_data, AddressAllInfos, header_meta):
        town_kladr = None
        if AddressAllInfos:
            town_kladr = self.get_town_kladr(AddressAllInfos[0])
        org_item['body'] = {
            'TFOMSCode': str(header_meta['remote_main_id']),  # id/code двух систем будут совпадать
            'full_name': clinic_data['name'],
            'short_name': clinic_data['name'],
            'address': clinic_data.get('actualAddress', ''),
            'area': town_kladr,
            'is_LPU': 1,
        }

    def get_town_kladr(self, address):
        for entry in address['data']:
            if entry['level'] == 4:
                return entry['kladrCode'][:11]
