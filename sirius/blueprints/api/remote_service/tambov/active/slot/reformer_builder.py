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
from sirius.lib.xform import Undefined
from sirius.models.system import SystemCode
from sirius.models.operation import OperationCode

encode = lambda x: x and WebMisJsonEncoder().default(x)


class SlotTambovBuilder(Builder):
    remote_sys_code = SystemCode.TAMBOV

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.DOCTOR: {
                'entity': TambovEntityCode.LOCATION, 'param': 'location'
            },
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
            times = self.get_times(reformed_req)
            for time_data in times:
                self.set_times(time_data, package, req_meta)
        elif req_meta['dst_operation_code'] == OperationCode.READ_ONE:
            self.set_times([req_meta['dst_id']], package, req_meta)
        else:
            raise InternalError('Unexpected dst_operation_code')
        return package

    def get_times(self, reformed_req):
        res = []
        today = date.today()
        for inc in range(1):
            time_data = today + timedelta(inc)
            req = reformed_req.copy()
            for param_name, param_data in req.meta['dst_parents_params'].items():
                req.data_update({
                    param_name: param_data['id'],
                    'date': time_data,
                })
            res.append(self.transfer__send_request(req))
        return res

    def set_times(self, time_data, package, req_meta):
        """
        getTime(location=<parent>, date=today+n)
        """
        time_item = package.add_main_pack_entity(
            entity_code=TambovEntityCode.TIME,
            method=req_meta.method,
            main_param_name='location',
            main_id=req_meta['dst_parents_params']['id'],
            parents_params=req_meta['dst_parents_params'],
            data=time_data,
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
            TambovEntityCode.LOCATION: {
                'entity': RisarEntityCode.DOCTOR, 'param': 'doctor_code'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        time_item = entities.set_main_entity(
            dst_entity_code=RisarEntityCode.SCHEDULE_TICKET,
            dst_parents_params=header_meta['local_parents_params'],
            dst_main_id_name='date',
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['remote_main_param_name'],
            src_id=header_meta['remote_main_id'],
            level_count=1,
        )
        if src_operation_code != OperationCode.DELETE:
            self.build_local_time_body(time_item, time_data, header_meta)

        return entities

    def build_local_time_body(self, time_item, time_data, header_meta):
        sch_intervals = []
        for time_interval in time_data['interval']:
            sch_interval = {
                'begin_time': time_interval['from'],
                'end_time': time_interval['to'],
                'quantity': 1,  # todo:
            }
            sch_intervals.append(sch_interval)
        time_item['body'] = {
            'date': time_data['date'],  # id/code двух систем будут совпадать
            'intervals': sch_intervals,
        }
