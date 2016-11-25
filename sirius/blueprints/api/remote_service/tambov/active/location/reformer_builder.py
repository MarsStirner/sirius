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
from sirius.blueprints.monitor.exception import InternalError, LoggedException
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = WebMisJsonEncoder().default


class LocationTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.ORGANIZATION: {
                'entity': TambovEntityCode.CLINIC, 'param': 'clinic'
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        req_data = self.build_remote_request_common(header_meta, dst_entity_code)
        return req_data

    ##################################################################
    ##  build packages by req

    def build_remote_entity_packages(self, reformed_req):
        package = EntitiesPackage(self, self.remote_sys_code)
        req_meta = reformed_req.meta
        if req_meta['dst_operation_code'] == OperationCode.READ_MANY:
            locations_ids = self.get_locations_ids(reformed_req)
            self.set_locations(locations_ids, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_locations([req_meta['dst_id']], package, req_meta)
        else:
            raise InternalError('Unexpected dst_operation_code')
        return package

    def get_locations_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({param_name: param_data['id']})
        res = self.transfer__send_request(req)
        return res

    def set_locations(self, locations_ids, package, req_meta):
        """
        getLocations(clinic=getPlaces.clinic)
        getLocation(location=getLocations.location)
        getEmployeePosition(id=getLocation.employeePosition)
        getEmployee(id=getEmployeePosition.employee)
        getIndividual(getIndividualRequest=getEmployee.individual)
        getEmployeeSpecialities(employee=getEmployeePosition.employee)
        """
        for location_id in locations_ids:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.LOCATION,
                OperationCode.READ_ONE,
            )
            loc_req = DataRequest()
            loc_req.set_req_params(
                url=api_method['template_url'],
                method=api_method['method'],
                data={'location': location_id},
            )
            try:
                location_data = self.transfer__send_request(loc_req)
            except LoggedException:
                continue

            for employeePosition in safe_traverse_attrs(location_data, 'employeePositionList', 'EmployeePosition') or []:
                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.EMPLOYEE_POSITION,
                    OperationCode.READ_ONE,
                )
                emp_pos_req = DataRequest()
                emp_pos_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    data={'id': employeePosition['employeePosition']},
                )
                employeePosition_data = self.transfer__send_request(emp_pos_req)

                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.EMPLOYEE_SPECIALITIES,
                    OperationCode.READ_MANY,
                )
                emp_spec_req = DataRequest()
                emp_spec_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    data={'employee': employeePosition_data['employee']},
                )
                empl_specs_list = self.transfer__send_request(emp_spec_req)
                for empl_spec_data in empl_specs_list:
                    location_item = package.add_main_pack_entity(
                        entity_code=TambovEntityCode.LOCATION,
                        method=loc_req.method,
                        main_param_name='location',
                        main_id=location_id,
                        parents_params=req_meta['dst_parents_params'],
                        data=location_data,
                    )
                    package.root_item = location_item

                    empl_pos_item = package.add_addition_pack_entity(
                        root_item=package.root_item,
                        parent_item=location_item,
                        entity_code=TambovEntityCode.EMPLOYEE_POSITION,
                        main_id=employeePosition['employeePosition'],
                        data=employeePosition_data,
                    )

                    empl_pos_item = package.add_addition_pack_entity(
                        root_item=package.root_item,
                        parent_item=empl_pos_item,
                        entity_code=TambovEntityCode.EMPLOYEE_SPECIALITIES,
                        main_id=employeePosition_data['employee'],
                        data=empl_spec_data,
                    )

                    employee_data = package.add_addition(
                        parent_item=empl_pos_item,
                        entity_code=TambovEntityCode.EMPLOYEE,
                        main_id_name='id',
                        main_id=employeePosition_data['employee'],
                    )

                    individual_data = package.add_addition(
                        parent_item=empl_pos_item,
                        entity_code=TambovEntityCode.INDIVIDUAL,
                        main_id_name=None,
                        main_id=employee_data['individual'],
                    )

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        location_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        # params_map = {
        #     TambovEntityCode.PATIENT: {
        #         'entity': RisarEntityCode.CARD, 'param': 'card_id'
        #     }
        # }
        # self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        location_addition = pack_entity['addition']
        empl_posit = location_addition[TambovEntityCode.EMPLOYEE_POSITION][0]
        empl_special = location_addition[TambovEntityCode.EMPLOYEE_SPECIALITIES][0]
        empl_posit_data = empl_posit['data']
        empl_special_data = empl_special['data']
        entities = RequestEntities()
        doctor_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.DOCTOR,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='regional_code',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id='_'.join((
                location_data['main_id'],
                empl_posit_data['main_id'],
                empl_special_data['main_id'],
            )),
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            self.build_local_doctor_body(doctor_item, location_data, empl_posit_data, header_meta)

        return entities

    def build_local_doctor_body(self, doctor_item, location_data, employeePosition_data, header_meta):
        location_adds = employeePosition_data['addition']
        empl_pos = location_adds[TambovEntityCode.EMPLOYEE_POSITION]
        employee = location_adds[TambovEntityCode.EMPLOYEE]
        individual = location_adds[TambovEntityCode.INDIVIDUAL]
        spec = location_adds[TambovEntityCode.EMPLOYEE_SPECIALITIES]
        doctor_item['body'] = {
            'regional_code': employeePosition_data['main_id'],  # id/code двух систем будут совпадать
            'organization': header_meta['remote_main_id'],  # id/code двух систем будут совпадать
            'last_name': individual['surname'],
            'first_name': individual['name'],
            'sex': individual['gender'],
            'SNILS': '0',
            'INN': '0',
            'speciality': spec['speciality'],
            'post': empl_pos['position'],
        }
