#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime, timedelta
import xml.etree.ElementTree as ET

from hitsl_utils.safe import safe_traverse, safe_int
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.remote_service.tambov.active.connect import \
    RequestModeCode
from sirius.blueprints.api.remote_service.tula.entities import \
    TulaEntityCode
from sirius.blueprints.monitor.exception import InternalError
from sirius.blueprints.reformer.api import Builder, EntitiesPackage, \
    RequestEntities, DataRequest
from sirius.blueprints.reformer.models.matching import MatchingId
from sirius.lib.apiutils import ApiException
from sirius.lib.xform import Undefined
from sirius.models.operation import OperationCode
from sirius.models.protocol import ProtocolCode
from sirius.models.system import SystemCode


class ScheduleTulaBuilder(Builder):
    remote_sys_code = SystemCode.TULA

    ##################################################################
    ##  reform requests

    def build_remote_request(self, header_meta, dst_entity_code):
        # сопоставление параметров родительских сущностей
        src_entity_code = header_meta['local_entity_code']
        params_map = {
            RisarEntityCode.ORGANIZATION: {
                'entity': TulaEntityCode.ORGANIZATION, 'param': 'DCODE'
            },
            RisarEntityCode.DOCTOR: {
                'entity': TulaEntityCode.DOCTOR, 'param': 'DCODE'
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
        schedules = self.get_schedules(reformed_req, package)
        self.set_schedule_idents(schedules, package, req_meta)
        return package

    def get_schedules(self, reformed_req, package):
        res = []
        package.enable_diff_check()
        package.enable_delete_check()

        for param_name, param_data in reformed_req.meta['dst_parents_params'].items():
            reformed_req.data_update({param_name: param_data['id']})

        doct_code = reformed_req.meta['dst_parents_params'][TulaEntityCode.DOCTOR]['id']
        today = datetime.today().date()

        # todo: TEST
        # doct_code = '120000186'
        # today = datetime(2016, 12, 14).date()

        begin_date = today.isoformat().replace('-', '')
        end_date = (today + timedelta(weeks=2)).isoformat().replace('-', '')
        # # todo: для тестов 2 дня
        # end_date = (today + timedelta(2)).isoformat().replace('-', '')
        diff_key_beg = '_'.join((doct_code, begin_date))
        diff_key_end = '_'.join((doct_code, end_date))
        package.set_diff_key_range((diff_key_beg, diff_key_end))

        doct_sch_req_data = self.get_doct_sch_req_data(doct_code, begin_date, end_date)
        doct_sch_req = reformed_req.copy()
        doct_sch_req.set_req_mode(RequestModeCode.XML_DATA)
        doct_sch_req.req_data['body'] = doct_sch_req_data
        doct_schedules = self.transfer__send_request(doct_sch_req)
        find_prefix = './/{http://sdsys.ru/}'

        doct_schedule_frst = doct_schedules.find(find_prefix + 'DOCTSCHED')
        if doct_schedule_frst:
            filial_code = doct_schedule_frst.findtext(find_prefix + 'FILIAL')
            self.save_doct_filial(doct_code, filial_code)

        for doct_sch_data in doct_schedules.findall(find_prefix + 'DOCTSCHED'):
            sch_req_data = self.get_sch_req_data(doct_sch_data.findtext(find_prefix + 'FILIAL'),
                                                 doct_sch_data.findtext(find_prefix + 'SCHEDIDENT'),
                                                 begin_date, end_date)
            sch_req = reformed_req.copy()
            sch_req.req_data['body'] = sch_req_data
            sch_data = self.transfer__send_request(sch_req)
            for DOCTSCHED in sch_data.findall(find_prefix + 'DEP'):
                for DOCT in DOCTSCHED.findall(find_prefix + 'DOCT'):
                    for WRDATE in DOCT.findall(find_prefix + 'WRDATE'):
                        for SCHEDINT in WRDATE.findall(find_prefix + 'SCHEDINT'):
                            res.append((doct_sch_data, SCHEDINT))
        return res

    def set_schedule_idents(self, schedules, package, req_meta):
        find_prefix = './/{http://sdsys.ru/}'
        for doct_sch_data, SCHEDINT in schedules:
            diff_key = '_'.join((
                doct_sch_data.findtext(find_prefix + 'DCODE'),
                doct_sch_data.findtext(find_prefix + 'WDATE')
            ))
            schedule_data_el = ET.Element('schedule_data')
            schedule_data_el.append(doct_sch_data)
            schedule_data_el.append(SCHEDINT)

            item = package.add_main_pack_entity(
                entity_code=req_meta['src_entity_code'],
                method=req_meta['dst_method'],
                main_param_name='SCHEDIDENT',
                main_id=doct_sch_data.findtext(find_prefix + 'SCHEDIDENT'),
                parents_params=req_meta['src_parents_params'],
                data=schedule_data_el,
                diff_key=diff_key,
            )
        return package

    def get_doct_sch_req_data(self, doct_code, begin_date, end_date):
        # todo: переделать на сборку на xsd
        res = """
<WEB_DOCT_SCHEDULE xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>DOCT_SCHEDULE</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
    </MSH>
    <DOCT_SCHEDULE_IN>
        <DOCTLIST>{DCODEIN}</DOCTLIST>
        <BDATE>{BDATE}</BDATE>
        <FDATE>{FDATE}</FDATE>
    </DOCT_SCHEDULE_IN>
</WEB_DOCT_SCHEDULE>
                """.format(
            DCODEIN=doct_code,
            BDATE=begin_date,
            FDATE=end_date,
        )
        return res

    def get_sch_req_data(self, filial_code, sched_ident, begin_date, end_date):
        # todo: переделать на сборку на xsd
        res = """
<WEB_SCHEDULE xmlns="http://sdsys.ru/">
    <MSH>
        <MSH.7>
            <TS.1>20110302184008</TS.1>
        </MSH.7>
        <MSH.9>
            <MSG.1>WEB</MSG.1>
            <MSG.2>SCHEDULE</MSG.2>
        </MSH.9>
        <MSH.10>74C0ACA47AFE4CED2B838996B0DF5821</MSH.10>
        <MSH.18>UTF-8</MSH.18>
        <MSH.99>{FILIAL_CODE}</MSH.99>
    </MSH>
    <SCHEDULE_IN>
        <SCHEDIDENTLIST>{SCHEDIDENTLIST}</SCHEDIDENTLIST>
        <SHOWPATIENTINFO>1</SHOWPATIENTINFO>
        <BDATE>{BDATE}</BDATE>
        <FDATE>{FDATE}</FDATE>
    </SCHEDULE_IN>
</WEB_SCHEDULE>
            """.format(
                FILIAL_CODE=filial_code,
                SCHEDIDENTLIST=sched_ident,
                BDATE=begin_date,
                FDATE=end_date,
            )
        return res

    ##################################################################
    ##  reform entities to remote

    def build_local_entities(self, header_meta, pack_entity):
        sched_data = pack_entity['data']
        src_entity_code = header_meta['remote_entity_code']
        src_operation_code = self.get_operation_code_by_method(header_meta['remote_method'])

        # сопоставление параметров родительских сущностей
        params_map = {
            TulaEntityCode.ORGANIZATION: {
                'entity': RisarEntityCode.ORGANIZATION, 'param': 'organisation'
            },
            TulaEntityCode.DOCTOR: {
                'entity': RisarEntityCode.DOCTOR, 'param': 'doctor'
            },
        }
        self.reform_remote_parents_params(header_meta, src_entity_code, params_map)
        find_prefix = './/{http://sdsys.ru/}'

        entities = RequestEntities()
        main_item = entities.set_main_entity(
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
            doct_sch_data = sched_data.find(find_prefix + 'DOCTSCHED')
            SCHEDINT = sched_data.find(find_prefix + 'SCHEDINT')
            main_item['body'] = {
                'date': self.date_misf_mrf(doct_sch_data, find_prefix + 'WDATE'),
                'time_begin': self.time_misf_mrf(doct_sch_data, find_prefix + 'BEGHOUR', find_prefix + 'BEGMIN'),
                'time_end': self.time_misf_mrf(doct_sch_data, find_prefix + 'ENDHOUR', find_prefix + 'ENDMIN'),
                'doctor': header_meta['local_parents_params'][RisarEntityCode.DOCTOR]['id'],
                'hospital': header_meta['local_parents_params'][RisarEntityCode.ORGANIZATION]['id'],
            }
            build_schedule_tickets = []
            for INTERVAL in SCHEDINT.findall(find_prefix + 'INTERVAL'):
                build_schedule_tickets.append({
                    'time_begin': self.time_misf_mrf(INTERVAL, find_prefix + 'BHOUR', find_prefix + 'BMIN'),
                    'time_end': self.time_misf_mrf(INTERVAL, find_prefix + 'FHOUR', find_prefix + 'FMIN'),
                    'patient': INTERVAL.findtext(find_prefix + 'PCODE'),
                })
            main_item['body']['schedule_tickets'] = build_schedule_tickets

        return entities

    def date_misf_mrf(self, el, t):
        return datetime.strptime(el.findtext(t), '%Y%m%d').date().isoformat()

    def time_misf_mrf(self, el, t1, t2):
        return datetime.strptime(el.findtext(t1) + el.findtext(t2), '%H%M').time().isoformat()[:5]

    def save_doct_filial(self, doct_code, filial_code):
        if not filial_code:
            return
        self.reformer.update_remote_match_prefix(
            TulaEntityCode.DOCTOR,
            RisarEntityCode.DOCTOR,
            doct_code,
            filial_code,
        )
