#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

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
from sirius.models.protocol import ProtocolCode
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = lambda x: x and WebMisJsonEncoder().default(x)


class EmployeePositionTambovBuilder(Builder):
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
            employees_ids = self.get_employees_ids(reformed_req)
            package.enable_diff_check()
            diff_key = req_meta['dst_parents_params']['clinic']['id']
            package.set_diff_key_range((diff_key, diff_key))
            self.set_employees_positions(employees_ids, package, req_meta, diff_key)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_employees_positions([req_meta['dst_id']], package, req_meta)
        else:
            raise InternalError('Unexpected dst_operation_code')
        return package

    def get_employees_ids(self, reformed_req):
        req = reformed_req
        for param_name, param_data in req.meta['dst_parents_params'].items():
            req.data_update({param_name: param_data['id']})
        res = self.transfer__send_request(req)
        return res

    def set_employees_positions(self, employees_ids, package, req_meta, diff_key=None):
        """
        getEmployees(clinic=getPlaces.clinic)  # лпу из мр
        getEmployeePositions(employee=getEmployees.employee)
        getEmployeePosition(id=getEmployeePositions.employeePosition)
        getPosition(id=getEmployeePosition.position)
        getEmployee(id=getEmployeePosition.employee)
        getIndividual(getIndividualRequest=getEmployee.individual)
        """

        for employee_id in employees_ids:
            api_method = self.reformer.get_api_method(
                self.remote_sys_code,
                TambovEntityCode.EMPLOYEE_POSITION,
                OperationCode.READ_MANY,
            )
            empl_pos_req = DataRequest()
            empl_pos_req.set_req_params(
                url=api_method['template_url'],
                method=api_method['method'],
                protocol=ProtocolCode.SOAP,
                data={'employee': employee_id},
            )
            empl_positions_data = self.transfer__send_request(empl_pos_req)

            for empl_position_id in safe_traverse_attrs(
                empl_positions_data, 'EmployeePosition'
            ) or []:

                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.EMPLOYEE_POSITION,
                    OperationCode.READ_ONE,
                )
                emp_pos_req = DataRequest()
                emp_pos_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    protocol=ProtocolCode.SOAP,
                    data={'id': empl_position_id},
                )
                employeePosition_data = self.transfer__send_request(emp_pos_req)
                if not self.valid_employee_position(employeePosition_data):
                    continue

                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.POSITION,
                    OperationCode.READ_ONE,
                )
                emp_spec_req = DataRequest()
                emp_spec_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    protocol=ProtocolCode.SOAP,
                    data={'id': employeePosition_data['position']},
                )
                position_data = self.transfer__send_request(emp_spec_req)
                if not self.valid_position(position_data):
                    continue

                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.EMPLOYEE,
                    OperationCode.READ_ONE,
                )
                employee_req = DataRequest()
                employee_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    protocol=ProtocolCode.SOAP,
                    data={'id': employeePosition_data['employee']},
                )
                employee_data = self.transfer__send_request(employee_req)

                #####################################
                # add

                api_method = self.reformer.get_api_method(
                    self.remote_sys_code,
                    TambovEntityCode.INDIVIDUAL,
                    OperationCode.READ_ONE,
                )
                individual_req = DataRequest()
                individual_req.set_req_params(
                    url=api_method['template_url'],
                    method=api_method['method'],
                    protocol=ProtocolCode.SOAP,
                    options=(employee_data['individual'],),
                )
                individual_data = self.transfer__send_request(individual_req)
                location_item = package.add_main_pack_entity(
                    entity_code=TambovEntityCode.EMPLOYEE_POSITION,
                    method=empl_pos_req.method,
                    main_param_name='employeePosition',
                    main_id=empl_position_id,
                    parents_params=req_meta['dst_parents_params'],
                    data=individual_data,  # в эмплой позишн кладем индивид, т.к. первый не нужен в диффах
                    diff_key=diff_key,
                )

                package.add_addition_pack_entity(
                    root_item=package.root_item,
                    parent_item=location_item,
                    entity_code=TambovEntityCode.POSITION,
                    main_id=employeePosition_data['position'],
                    data=position_data,
                    diff_key=diff_key,
                )

    def valid_employee_position(self, employeePosition_data):
        today = datetime.today().date()
        if not (not employeePosition_data['endDate'] or
                employeePosition_data['endDate'] > today):
            return False
        return True

    def valid_position(self, position_data):
        # могут быть не только Акушеры-Геникологи
        # if not (position_data['role'] == '1034'):
        #     return False
        # if not (position_data['speciality'] == '1'):
        #     return False
        return True

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.CLINIC: {
                'entity': RisarEntityCode.ORGANIZATION, 'param': 'TFOMSCode'
            }
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        empl_pos_addition = pack_entity['addition']  # в эмплой позишн клали индивид, т.к. первый не нужен в диффах

        entities = RequestEntities()
        doctor_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.DOCTOR,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='regional_code',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=pack_entity['main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            self.build_local_doctor_body(doctor_item, pack_entity,
                                         empl_pos_addition, header_meta, pack_entity['main_id'])

        return entities

    def build_local_doctor_body(self, doctor_item, pack_entity,
                                empl_pos_addition, header_meta, src_id):
        # individual = location_addition[TambovEntityCode.INDIVIDUAL][0]
        position = empl_pos_addition[TambovEntityCode.POSITION][0]
        position_data = position['data']
        individual_data = pack_entity['data']
        doctor_item['body'] = {
            'regional_code': src_id,  # id/code двух систем будут совпадать
            'organization': header_meta['local_parents_params']['TFOMSCode']['id'],  # id/code двух систем будут совпадать
            'last_name': individual_data['surname'],
            'first_name': individual_data['name'],
            'patr_name': individual_data['patrName'] or '',
            'sex': safe_int(individual_data['gender']),
            'birth_date': encode(individual_data['birthDate']) or '',
            'speciality': position_data['speciality'],
            'post': position_data['role'],
        }
