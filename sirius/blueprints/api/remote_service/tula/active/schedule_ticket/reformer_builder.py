#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.lib.transfer import \
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
            RisarEntityCode.DOCTOR: {
                'entity': TulaEntityCode.DOCTOR, 'param': 'doctor'
            },
            RisarEntityCode.CLIENT: {
                'entity': TulaEntityCode.CLIENT, 'param': 'patient'
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)

        entities = RequestEntities(self.reformer.stream_id)

        remote_id_prefix = None
        if src_operation_code != OperationCode.DELETE:
            if schedule_ticket_data['schedule_ticket_type'] == '1':
                remote_id_prefix = 'outplan'
            else:
                remote_id_prefix = 'plan'

        def after_send_func(entity_meta, entity_body, answer_body):
            if src_operation_code != OperationCode.DELETE:
                res = self.reformer.update_local_match_parent(
                    RisarEntityCode.SCHEDULE_TICKET,
                    TulaEntityCode.SCHEDULE_TICKET,
                    schedule_ticket_data['schedule_ticket_id'],
                    matching_parent_id,
                )
                if not res:
                    raise InternalError(
                        u'Не удалось привязать тикет (%s) к родителю (%s)' %
                        (schedule_ticket_data['schedule_ticket_id'],
                         matching_parent_id)
                    )
        main_item = entities.set_main_entity(
            dst_entity_code=TulaEntityCode.SCHEDULE_TICKET,
            dst_parents_params=header_meta['remote_parents_params'],
            dst_main_id_name='schedule_ticket_id',
            dst_id_prefix=remote_id_prefix,
            src_operation_code=src_operation_code,
            src_entity_code=src_entity_code,
            src_main_id_name=header_meta['local_main_param_name'],
            after_send_func=after_send_func,
            src_id=header_meta['local_main_id'],
            level_count=1,
            dst_request_mode=RequestModeCode.XML_DATA,
        )
        remote_pp = header_meta['remote_parents_params']
        filial_code = self.get_filial_code(
            remote_pp['doctor']['id'],
            schedule_ticket_data['date'],
        )
        remote_sch_ticket_id = None
        if src_operation_code != OperationCode.ADD:
            remote_sch_ticket_id = self.reformer.get_remote_id_by_local(
                TulaEntityCode.SCHEDULE_TICKET,
                RisarEntityCode.SCHEDULE_TICKET,
                schedule_ticket_data['schedule_ticket_id'],
            )
        if src_operation_code != OperationCode.DELETE:
            matching_parent = self.reformer.get_by_local_id(
                TulaEntityCode.SCHEDULE,
                RisarEntityCode.SCHEDULE,
                schedule_ticket_data['schedule_id'],
            )
            matching_parent_id = matching_parent.id
            if schedule_ticket_data['schedule_ticket_type'] == '1':
                time_begin = schedule_ticket_data['time_begin'] or datetime.today().time().isoformat()[:5]
                sch_treat_add_req_data = self.get_sch_treat_add_req_data(
                    filial_code,
                    remote_pp['patient']['id'],
                    remote_pp['doctor']['id'],
                    schedule_ticket_data['date'],
                    remote_sch_ticket_id,
                    schedule_ticket_data['schedule_ticket_id'],
                    time_begin,
                )
                main_item['body'] = sch_treat_add_req_data
            else:
                remote_schedule_id = matching_parent.remote_id
                sched_reserve_req_data = self.get_sch_reserve_req_data(
                    filial_code,
                    remote_pp['patient']['id'],
                    remote_pp['doctor']['id'],
                    schedule_ticket_data['date'],
                    remote_schedule_id,
                    schedule_ticket_data['schedule_ticket_id'],
                    schedule_ticket_data['time_begin'],
                    schedule_ticket_data['time_end'],
                )
                main_item['body'] = sched_reserve_req_data
        else:
            if schedule_ticket_data['schedule_ticket_type'] == '1':
                today = datetime.today()
                today_date = today.date()
                today_time = today.time()
                sched_remove_req_data = self.get_sch_treat_remove_req_data(
                    filial_code,
                    remote_pp['patient']['id'],
                    remote_pp['doctor']['id'],
                    schedule_ticket_data['date'],
                    remote_sch_ticket_id,
                    schedule_ticket_data['schedule_ticket_id'],
                    today_time.isoformat()[:5],
                    today_date.isoformat(),
                    schedule_ticket_data['current_person'],
                )
                main_item['body'] = sched_remove_req_data
            else:
                sched_remove_req_data = self.get_sch_remove_req_data(
                    filial_code,
                    remote_pp['patient']['id'],
                    remote_sch_ticket_id,
                )
                main_item['body'] = sched_remove_req_data

        return entities

    def get_sch_reserve_req_data(
        self, filial_code, p_code, d_code, workdate,
        schedident, ext_schedid, beg_time, end_time
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
        <AUTHMODE>4</AUTHMODE>
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
            EXTSCHEDID=ext_schedid,
        )
        return res

    def get_sch_remove_req_data(
        self, filial_code, p_code, schedid
    ):
        # todo: переделать на сборку на xsd
        res = """
<WEB_SCHEDULE_REC_REMOVE xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>SCHEDULE_REC_REMOVE</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
        <MSH.99>{FILIAL_CODE}</MSH.99>
    </MSH>
    <SCHEDULE_REC_REMOVE_IN>
        <SCHEDID>{SCHEDID}</SCHEDID>
        <PCODE>{PCODE}</PCODE>
    </SCHEDULE_REC_REMOVE_IN>
</WEB_SCHEDULE_REC_REMOVE>
        """.format(
            FILIAL_CODE=filial_code,
            PCODE=p_code,
            SCHEDID=schedid,
        )
        return res

    def get_doctor_req_data(
        self, d_code, bdate, fdate
    ):
        # todo: переделать на сборку на xsd
        res = """
<WEB_GET_DOCTOR_LIST xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>GET_DOCTOR_LIST</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
    </MSH>
    <GET_DOCTOR_LIST_IN>
        <BDATE>{BDATE}</BDATE>
        <FDATE>{FDATE}</FDATE>
        <DCODEIN>{DCODEIN}</DCODEIN>
    </GET_DOCTOR_LIST_IN>
</WEB_GET_DOCTOR_LIST>
        """.format(
            BDATE=bdate.replace('-', ''),
            FDATE=fdate.replace('-', ''),
            DCODEIN=d_code,
        )
        return res

    def get_filial_code(self, doc_code, workdate):
        sched_reserve_req_data = self.get_doctor_req_data(
            doc_code,
            workdate,
            workdate,
        )

        sched_reserve_req = DataRequest(self.reformer.stream_id)
        sched_reserve_req.set_meta(
            dst_system_code=self.remote_sys_code,
            dst_entity_code=TulaEntityCode.SCHEDULE,
            dst_operation_code=OperationCode.ADD,
            dst_id=None,
            dst_parents_params={},
        )
        sched_reserve_req.set_req_mode(RequestModeCode.XML_DATA)
        self.reformer.set_request_service(sched_reserve_req)
        sched_reserve_req.req_data['body'] = sched_reserve_req_data
        req_result = self.transfer__send_request(sched_reserve_req)
        find_prefix = './/{http://sdsys.ru/}'
        doct_list_frst = req_result.find(find_prefix + 'GETDOCTORLIST')
        if doct_list_frst:
            res = doct_list_frst.findtext(find_prefix + 'FILIAL')
        else:
            raise InternalError('Not found filial for doctor with code = (%s); workdate = (%s)' %
                                (doc_code, workdate))
        return res

    def get_sch_treat_add_req_data(
        self, filial_code, p_code, d_code, workdate,
        streatid, ext_streatid, beg_time
    ):
        # todo: переделать на сборку на xsd
        b_hour, b_min = beg_time.split(':')
        res = """
<WEB_SCHEDTREATS_ADD xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>SCHEDTREAT_ADD</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
        <MSH.99>{FILIAL_CODE}</MSH.99>
    </MSH>
    <SCHEDTREAT_ADD_IN>
        <DCODE>{DCODE}</DCODE>
        <WORKDATE>{WORKDATE}</WORKDATE>
        <BHOUR>{BHOUR}</BHOUR>
        <BMIN>{BMIN}</BMIN>
        <PCODE>{PCODE}</PCODE>
        <STREATID>{STREATID}</STREATID>
        <EXTSTREATID>{EXTSTREATID}</EXTSTREATID>
    </SCHEDTREAT_ADD_IN>
</WEB_SCHEDTREATS_ADD>
        """.format(
            FILIAL_CODE=filial_code,
            DCODE=d_code,
            WORKDATE=workdate.replace('-', ''),
            BHOUR=int(b_hour),
            BMIN=int(b_min),
            PCODE=p_code,
            STREATID=streatid or '',
            EXTSTREATID=ext_streatid,
        )
        return res

    def get_sch_treat_remove_req_data(
        self, filial_code, p_code, d_code, workdate,
        streatid, ext_streatid, beg_time, remdate, rd_code
    ):
        # todo: переделать на сборку на xsd
        b_hour, b_min = beg_time.split(':')
        res = """
<WEB_SCHEDTREATS_ADD xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>SCHEDTREAT_ADD</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
        <MSH.99>{FILIAL_CODE}</MSH.99>
    </MSH>
    <SCHEDTREAT_ADD_IN>
        <DCODE>{DCODE}</DCODE>
        <WORKDATE>{WORKDATE}</WORKDATE>
        <BHOUR>{BHOUR}</BHOUR>
        <BMIN>{BMIN}</BMIN>
        <PCODE>{PCODE}</PCODE>
        <REMDATE>{REMDATE}</REMDATE>
        <REMUID>{REMUID}</REMUID>
        <STREATID>{STREATID}</STREATID>
        <EXTSTREATID>{EXTSTREATID}</EXTSTREATID>
    </SCHEDTREAT_ADD_IN>
</WEB_SCHEDTREATS_ADD>
        """.format(
            FILIAL_CODE=filial_code,
            DCODE=d_code,
            WORKDATE=workdate.replace('-', ''),
            BHOUR=int(b_hour),
            BMIN=int(b_min),
            PCODE=p_code,
            REMDATE=remdate.replace('-', ''),
            REMUID=rd_code,
            STREATID=streatid,
            EXTSTREATID=ext_streatid,
        )
        return res
