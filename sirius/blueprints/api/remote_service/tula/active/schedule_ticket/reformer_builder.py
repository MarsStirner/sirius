#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.active.connect import \
    RequestModeCode
from sirius.blueprints.api.remote_service.tula.entities import \
    TulaEntityCode
from sirius.blueprints.monitor.exception import InternalError, ExternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.system import SystemCode


class ScheduleTicketTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  build packages by msg

    def build_local_entity_packages(self, msg):
        package = EntitiesPackage(self, SystemCode.LOCAL)
        msg_meta = msg.get_relative_meta()
        msg_meta['src_operation_code'] = self.get_operation_code_by_method(msg_meta['src_method'])
        schedule_ticket_data = msg.get_data()

        # дополнение параметров сущностью, если не указана
        params_meta = {
            # 'hospital': RisarEntityCode.ORGANIZATION,
            'doctor': RisarEntityCode.DOCTOR,
            'patient': RisarEntityCode.CLIENT,
        }
        self.set_src_parents_entity(msg_meta, params_meta)

        src_entity = msg_meta['src_entity_code']

        item = package.add_main_pack_entity(
            entity_code=src_entity,
            operation_code=msg_meta['src_operation_code'],
            method=msg_meta['dst_method'],
            main_param_name='schedule_ticket_id',
            main_id=msg_meta['src_main_id'],
            parents_params=msg_meta['src_parents_params'],
            data=schedule_ticket_data,
        )
        return package

    ##################################################################
    ##  reform entities to remote

    def build_remote_entities(self, header_meta, pack_entity):
        """
        Вход в header_meta
        local_operation_code
        local_entity_code
        local_main_param_name
        local_main_id
        local_parents_params

        Выход в entity
        dst_entity_code
        dst_main_param_name
        """
        schedule_ticket_data = pack_entity['data']
        src_operation_code = header_meta['local_operation_code']
        src_entity_code = header_meta['local_entity_code']

        # сопоставление параметров родительских сущностей
        params_map = {
            # RisarEntityCode.ORGANIZATION: {
            #     'entity': TulaEntityCode.ORGANIZATION, 'param': 'hospital'
            # },
            RisarEntityCode.DOCTOR: {
                'entity': TulaEntityCode.DOCTOR, 'param': 'doctor'
            },
            RisarEntityCode.CLIENT: {
                'entity': TulaEntityCode.CLIENT, 'param': 'patient'
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities()
        # main_item = entities.set_main_entity(
        #     dst_entity_code=TulaEntityCode.SCHEDULE_TICKET,
        #     dst_parents_params=header_meta['remote_parents_params'],
        #     dst_main_id_name='schedule_ticket_id',
        #     src_operation_code=src_operation_code,
        #     src_entity_code=src_entity_code,
        #     src_main_id_name=header_meta['local_main_param_name'],
        #     src_id=header_meta['local_main_id'],
        #     level_count=1,
        #     dst_request_mode=RequestModeCode.XML_DATA,
        # )
        # if src_operation_code != OperationCode.DELETE:
        schedule_id = self.reformer.get_remote_id_by_local(
            TulaEntityCode.SCHEDULE,
            RisarEntityCode.SCHEDULE,
            schedule_ticket_data['schedule_id'],
        )
        remote_pp = header_meta['remote_parents_params']
        filial_code = self.reformer.get_prefix_by_remote_id(
            RisarEntityCode.DOCTOR,
            TulaEntityCode.DOCTOR,
            remote_pp[TulaEntityCode.DOCTOR]['id'],
        )
        sched_reserve_req_data = self.get_sch_reserve_req_data(
            filial_code,
            remote_pp[TulaEntityCode.CLIENT]['id'],
            remote_pp[TulaEntityCode.DOCTOR]['id'],
            schedule_ticket_data['date'],
            schedule_id,
            schedule_ticket_data['schedule_ticket_id'],
            schedule_ticket_data['time_begin'],
            schedule_ticket_data['time_end'],
        )

        sched_reserve_req = DataRequest()
        sched_reserve_req.set_meta(
            dst_system_code=self.remote_sys_code,
            dst_entity_code=TulaEntityCode.SCHEDULE_TICKET,
            dst_operation_code=OperationCode.ADD,
            dst_id=None,
            dst_parents_params={},
        )
        sched_reserve_req.set_req_mode(RequestModeCode.XML_DATA)
        self.reformer.set_request_service(sched_reserve_req)
        sched_reserve_req.req_data['body'] = sched_reserve_req_data
        req_result = self.transfer__send_request(sched_reserve_req)
        res = req_result.findtext('SPRESULT')
        if res != '1':
            raise ExternalError('Reject reserve ticket %s' % schedule_ticket_data['schedule_ticket_id'])

        return entities

    def get_sch_reserve_req_data(
        self, filial_code, p_code, d_code, workdate,
        schedident, ext_schedident, beg_time, end_time
    ):
        # todo: переделать на сборку на xsd
        b_hour, b_min = beg_time.split(':')
        f_hour, f_min = end_time.split(':')
        res = """
<WEB_SCHEDULE_REC_RESERVE xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>SCHEDULE_REC_RESERVE</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
        <MSH.99>{FILIAL_CODE}</MSH.99>
    </MSH>
    <SCHEDULE_REC_RESERVE_IN>
        <PCODE>{PCODE}</PCODE>
        <DCODE>{DCODE}</DCODE>
        <WORKDATE>{WORKDATE}</WORKDATE>
        <SCHEDIDENT>{SCHEDIDENT}</SCHEDIDENT>
        <BHOUR>{BHOUR}</BHOUR>
        <BMIN>{BMIN}</BMIN>
        <FHOUR>{FHOUR}</FHOUR>
        <FMIN>{FMIN}</FMIN>
        <EXTSCHEDID>{EXTSCHEDID}</EXTSCHEDID>
    </SCHEDULE_REC_RESERVE_IN>
</WEB_SCHEDULE_REC_RESERVE>
        """.format(
            FILIAL_CODE=filial_code,
            PCODE=p_code,
            DCODE=d_code,
            WORKDATE=workdate.replace('-', ''),
            SCHEDIDENT=schedident,
            BHOUR=int(b_hour),
            BMIN=int(b_min),
            FHOUR=int(f_hour),
            FMIN=int(f_min),
            EXTSCHEDID=ext_schedident,
        )
        return res
