#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, timedelta

from hitsl_utils.safe import safe_traverse_attrs, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.entities import \
    TambovEntityCode
from sirius.blueprints.monitor.exception import InternalError, LoggedException
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.method import ApiMethod
from sirius.lib.message import Message
from sirius.lib.xform import Undefined
from sirius.models.protocol import ProtocolCode
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = lambda x: x and WebMisJsonEncoder().default(x)


class TimeTambovBuilder(Builder):
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
            package.enable_diff_check()
            clinic_id = req_meta['dst_parents_params']['clinic']['id']
            clinic_sched = []
            today = date.today()
            # today = date(2016, 12, 29)  # todo для тестов
            # range_val = 14
            range_val = 7  # todo для тестов
            max_date = today + timedelta(range_val)
            package.set_diff_key_range((
                '_'.join((str(clinic_id), today.isoformat())),
                '_'.join((str(clinic_id), max_date.isoformat()))
            ))
            locations_set = set()
            # for prototype_id in (5201,):  # todo для тестов Прием врача-акушера-гинеколога
            for prototype_id in (5202, 5203):  # первичный и повторный осмотр
                services = self.get_services(clinic_id, prototype_id)
                for service_data in services:
                    locations = self.get_locations(clinic_id, service_data['id'])
                    locations_set.update(locations)
            for location_id in locations_set:
                # if location_id not in ('14813',):  # todo для тестов
                #     continue
                employee_position_id = self.get_employee_position(location_id)
                if employee_position_id:
                    for inc in range(range_val):
                        sched_date = today + timedelta(inc)
                        sched_date_iso = sched_date.isoformat()
                        times = self.get_times(reformed_req, sched_date, location_id)
                        for time_data in times['timePeriod']:
                            self.set_times(clinic_sched, time_data, sched_date_iso, employee_position_id)
                        slots = self.get_reserved(sched_date, location_id)
                        for slot_data in slots:
                            if slot_data['status'] == '4':
                                # отмененная запись
                                continue
                            self.set_reserved(clinic_sched, slot_data, sched_date_iso, employee_position_id)
            self.set_package_data(package, reformed_req, req_meta, clinic_sched, clinic_id)
        # elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
        #     self.set_times([req_meta['dst_id']], package, req_meta)
        else:
            raise InternalError('Unexpected dst_operation_code')
        return package

    def get_services(self, clinic_id, prototype_id):
        service_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.SERVICE,
            OperationCode.READ_MANY,
        )
        req = DataRequest(self.reformer.stream_id)
        req.set_req_params(
            url=service_api_method['template_url'],
            method=service_api_method['method'],
            protocol=ProtocolCode.SOAP,
            data={'clinic': clinic_id, 'prototype': prototype_id},
        )
        res = self.transfer__send_request(req)
        return res

    def get_locations(self, clinic_id, service_id):
        location_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.LOCATION,
            OperationCode.READ_MANY,
        )
        req = DataRequest(self.reformer.stream_id)
        req.set_req_params(
            url=location_api_method['template_url'],
            method=location_api_method['method'],
            protocol=ProtocolCode.SOAP,
            data={'clinic': clinic_id, 'service': service_id},
        )
        res = self.transfer__send_request(req)
        return res

    def get_employee_position(self, location_id):
        location_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.LOCATION,
            OperationCode.READ_ONE,
        )
        req = DataRequest(self.reformer.stream_id)
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

    def get_times(self, reformed_req, sched_date, location_id):
        req = reformed_req.copy()
        req.req_data['body'] = {
            'location': location_id,
            'date': sched_date,
        }
        res = self.transfer__send_request(req)
        return res

    def set_times(self, clinic_sched, time_data, sched_date_iso, employee_position_id):
        if not (time_data['from'] and time_data['to']):
            return
        clinic_sched.append({
            'date': sched_date_iso,
            'employee_pos': employee_position_id,
            'beg': time_data['from'],
            'end': time_data['to'],
        })

    def get_reserved(self, sched_date, location_id):
        reserv_api_method = self.reformer.get_api_method(
            self.remote_sys_code,
            TambovEntityCode.RESERVE_FILTERED,
            OperationCode.READ_MANY,
        )
        req = DataRequest(self.reformer.stream_id)
        req.set_req_params(
            url=reserv_api_method['template_url'],
            method=reserv_api_method['method'],
            protocol=ProtocolCode.SOAP,
            data={'location': location_id, 'date': sched_date},
        )
        res = self.transfer__send_request(req)
        return res

    def set_reserved(self, clinic_sched, slot_data, times_date_iso, employee_position_id):
        # могут быть экстренные пациенты без времени
        if not (slot_data['timePeriod']['from'] and slot_data['timePeriod']['to']):
            return
        clinic_sched.append({
            'date': times_date_iso,
            'employee_pos': employee_position_id,
            'beg': slot_data['timePeriod']['from'],
            'end': slot_data['timePeriod']['to'],
            'patient': slot_data['patient']['patientId'],
        })

    def set_package_data(self, package, reformed_req, req_meta, clinic_sched, clinic_id):
        grouped_schedule = {}
        for clinic_sched_data in clinic_sched:
            key = (clinic_id, clinic_sched_data['date'], clinic_sched_data['employee_pos'])
            if key in grouped_schedule:
                work_interval = grouped_schedule[key]['work_interval']
                if clinic_sched_data['beg'] < work_interval['work_beg']:
                    work_interval['work_beg'] = clinic_sched_data['beg']
                if clinic_sched_data['end'] > work_interval['work_end']:
                    work_interval['work_end'] = clinic_sched_data['end']
            else:
                grouped_schedule[key] = {
                    'employee_pos': clinic_sched_data['employee_pos'],
                    'date': clinic_sched_data['date'],
                    'work_interval': {
                        'work_beg': clinic_sched_data['beg'],
                        'work_end': clinic_sched_data['end'],
                    },
                }
            grouped_schedule[key].setdefault('slots', []).append({
                'slot_beg': clinic_sched_data['beg'],
                'slot_end': clinic_sched_data['end'],
                'patient': clinic_sched_data.get('patient'),
            })
        for key, data in grouped_schedule.iteritems():
            time_item = package.add_main_pack_entity(
                entity_code=TambovEntityCode.TIME,
                method=reformed_req.method,
                main_param_name='clinic_date_emplPosition',
                main_id='_'.join(key),
                parents_params=req_meta['dst_parents_params'],
                data=data,
                diff_key='_'.join((str(clinic_id), data['date'])),
            )

    ##################################################################
    ##  reform entities

    def build_local_entities(self, header_meta, pack_entity):
        time_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = header_meta['remote_operation_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            TambovEntityCode.CLINIC: {
                'entity': RisarEntityCode.ORGANIZATION, 'param': 'lpu_code'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities(self.reformer.stream_id)
        doctor_code = self.reformer.find_local_id_by_remote(
            RisarEntityCode.DOCTOR,
            TambovEntityCode.EMPLOYEE_POSITION,
            time_data['employee_pos'],
        )
        if not doctor_code:
            return entities

        time_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.SCHEDULE,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='schedule_id',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            time_item['body'] = {
                # 'schedule_id': None,  # заполняется в set_current_id_func
                'hospital': header_meta['local_parents_params']['lpu_code']['id'],
                'doctor': doctor_code,
                'date': time_data['date'],
                'time_begin': time_data['work_interval']['work_beg'].isoformat()[:5],
                'time_end': time_data['work_interval']['work_end'].isoformat()[:5],
            }
            for slot_data in time_data['slots']:
                patient = None
                if slot_data['patient']:
                    patient_code = self.reformer.find_local_id_by_remote(
                        RisarEntityCode.CLIENT,
                        TambovEntityCode.SMART_PATIENT,
                        slot_data['patient'],
                    )
                    if not patient_code:
                        if self.request_patient(slot_data['patient']):
                            patient_code = self.reformer.find_local_id_by_remote(
                                RisarEntityCode.CLIENT,
                                TambovEntityCode.SMART_PATIENT,
                                slot_data['patient'],
                            )
                    # 2 - ИД псевдо пациента "Занято". Бывает нужен,
                    # если занято мужчиной, либо пациент еще не приходил
                    patient = patient_code or '2'

                time_item['body'].setdefault('schedule_tickets', []).append({
                    'time_begin': slot_data['slot_beg'].isoformat()[:5],
                    'time_end': slot_data['slot_end'].isoformat()[:5],
                    'patient': patient or Undefined,
                    'schedule_ticket_type': '0',
                })

        return entities

    def request_patient(self, patient_uid):
        from sirius.blueprints.api.local_service.producer import LocalProducer
        msg = Message(None, self.reformer.stream_id)
        msg.to_remote_service()
        msg.set_request_type()
        meta = msg.get_header().meta
        meta['local_operation_code'] = OperationCode.READ_ONE
        meta['remote_system_code'] = self.remote_sys_code
        meta['remote_entity_code'] = TambovEntityCode.SMART_PATIENT
        meta['remote_main_id'] = patient_uid
        prod = LocalProducer()
        try:
            res = prod.send(msg)
        except LoggedException:
            res = False
        return res
