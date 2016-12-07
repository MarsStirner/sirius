#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from datetime import date, datetime

from hitsl_utils.safe import safe_traverse, safe_int, safe_traverse_attrs, \
    safe_bool_none, safe_double, safe_bool
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

encode = lambda x: x and WebMisJsonEncoder().default(x)
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
                'entity': TambovEntityCode.SMART_PATIENT, 'param': 'patientUid'
            },
        }
        self.reform_local_parents_params(header_meta, src_entity_code, params_map)
        # todo для отладки по дев стенду
        # header_meta['remote_parents_params']['patientUid']['id'] = '5568693'

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
            TambovEntityCode.SMART_PATIENT: {
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
            part2 = birth_data['Part2']
            part3 = birth_data['Part3']
            part4 = birth_data['Part4']
            part5 = birth_data['Part5']
            part6 = birth_data['Part6']
            days = safe_int(safe_traverse_attrs(part1, 'PregnantTimeSpan', 'Days'))
            main_item['body'] = {
                # "required": ["admission_date", "pregnancy_duration",
                #              "delivery_date", "delivery_time",
                #              "maternity_hospital", "diagnosis_osn",
                #              "pregnancy_final"]
                'general_info': {
                    'admission_date': encode(part1['InDate']),
                    'maternity_hospital': safe_traverse_attrs(part1, 'BornClinic', 'OMS'),
                    'delivery_date': encode(safe_traverse_attrs(part1, 'ChildBirth', 'Date')),
                    'delivery_time': encode(safe_traverse_attrs(part1, 'ChildBirth', 'Time')),
                    'pregnancy_final': safe_traverse_attrs(part1, 'ChildBirth', 'ChildBirthOutcome'),  # rbRisarPregnancy_Final
                    # 'pregnancy_duration': safe_traverse_attrs(part1, 'ChildBirth', 'PregnantWeeks'),
                    'pregnancy_duration': days and int(days / 7) or 0,
                    'diagnosis_osn': 'A01.1',  # part1['Diagnoses']['Main'],
                    # --
                    # 'diagnosis_sop': part1['Extra'] or Undefined,
                    # 'diagnosis_osl': part1['Complication'] or Undefined,
                    'maternity_hospital_doctor': safe_traverse_attrs(part1, 'ChildBirth', 'Employee', 'FirstName') or Undefined,
                    'curation_hospital': part1['OrgName'] or Undefined,
                    'pregnancy_speciality': part1['BirthSpeciality'] or Undefined,
                    'postnatal_speciality': part1['AfterBirthSpeciality'] or Undefined,
                    'help': part1['HelpProvided'] or Undefined,
                    'abortion': part1['Abort'] or Undefined,
                    # 'death': ???,
                },
                # "required": [
                #     "reason_of_death",
                #     "death_date",
                #     "death_time"
                # ]
                'mother_death': {
                    'death_date': safe_traverse_attrs(part2, 'MotherDeathData', 'DeathDate'),
                    'death_time': safe_traverse_attrs(part2, 'MotherDeathData', 'DeathTime'),
                    'reason_of_death': safe_traverse_attrs(part2, 'MotherDeathData', 'MotherDeathReason'),
                    # --
                    # 'pat_diagnosis_osn': safe_traverse_attrs(part2, 'MotherDeathData', 'PatologicalDiagnos'),
                    # 'pat_diagnosis_sop': safe_traverse_attrs(part2, 'MotherDeathData', 'AcompanyDiagnos'),
                    # 'pat_diagnosis_osl': safe_traverse_attrs(part2, 'MotherDeathData', 'ComplicationDiagnos'),
                    'control_expert_conclusion': part2['LkkResult'] or Undefined,
                },
                'complications': {
                    'delivery_waters': part3['BirthWaterBreak'] or Undefined,
                    'pre_birth_delivery_waters': safe_bool_none(part3['PrenatalWaterBreak']) or Undefined,
                    'weakness': part3['BirthPowerWeakness'] or Undefined,
                    'meconium_color': safe_bool_none(part3['AmiaticWater']) or Undefined,
                    'pathological_preliminary_period': safe_bool_none(part3['PatologicPreliminaryPeriod']) or Undefined,
                    'abnormalities_of_labor': safe_bool_none(part3['BirthActivityAnomaly']) or Undefined,
                    'chorioamnionitis': safe_bool_none(part3['Horiamnionit']) or Undefined,
                    'perineal_tear': part3['PerinealRupture'] or Undefined,
                    'eclampsia': part3['Nefropaty'] or Undefined,
                    'anemia': safe_bool_none(part3['Anemia']) or Undefined,
                    'infections_during_delivery': part3['InfectionDuringBirth'] or Undefined,
                    'infections_after_delivery': part3['InfectionAfterBirth'] or Undefined,
                    'funiculus': safe_traverse_attrs(part3, 'CordPatology', 'Term') or Undefined,
                    'afterbirth': safe_traverse_attrs(part3, 'PlacentaPatology', 'Term') or Undefined,
                },
                'manipulations': {
                    'caul': safe_bool_none(part4['Amniotomy']) or Undefined,
                    'calfbed': safe_bool_none(part4['ManualWombSurvey']) or Undefined,
                    'perineotomy': part4['Perineotomy'] or Undefined,
                    'secundines': safe_bool_none(part4['ManualRemovalAfterBirth']) or Undefined,
                    'other_manipulations': part4['AnotherManipulations'] or Undefined,
                },
                'operations': {
                    'caesarean_section': part5['CesarianDelivery'] or Undefined,
                    'obstetrical_forceps': part5['Forceps'] or Undefined,
                    'vacuum_extraction': safe_bool_none(part5['Vacuum']),
                    'indication': part5['Indicator'] or Undefined,
                    'specialities': part5['Speciality'] or Undefined,
                    'anesthetization': part5['Anestesia'] or Undefined,
                    'hysterectomy': part5['Hysterectomy'] or Undefined,
                    # 'complications': part5['Complication'] or Undefined,
                    'embryotomy': part5['Embryotomy'] or Undefined,
                },
                'kids': []
            }
            kids = []
            childs = part6['Child']
            for child in childs:
                # "required": ["alive", "sex", "weight", "length", "date"]
                kids.append({
                    'alive': not safe_bool(safe_traverse_attrs(child, 'Child', 'IsDeath')),
                    'sex': safe_int(safe_traverse_attrs(child, 'Child', 'Gender')),
                    'weight': safe_double(safe_traverse_attrs(child, 'Child', 'Weight')),
                    'length': safe_double(safe_traverse_attrs(child, 'Child', 'Height')),
                    'date': encode(safe_traverse_attrs(child, 'Child', 'BirthDate')),
                    # --
                    # 'time': ???,
                    'maturity_rate': safe_traverse_attrs(child, 'Child', 'FullTerm') or Undefined,
                    'apgar_score_1': safe_int(safe_traverse_attrs(child, 'Child', 'Apgar_1min')) or Undefined,
                    'apgar_score_5': safe_int(safe_traverse_attrs(child, 'Child', 'Apgar_5min')) or Undefined,
                    'apgar_score_10': safe_int(safe_traverse_attrs(child, 'Child', 'Apgar_10min')) or Undefined,
                    'death_date': encode(safe_traverse_attrs(child, 'Child', 'DeathDate')) or Undefined,
                    'death_time': encode(safe_traverse_attrs(child, 'Child', 'DeathTime')) or Undefined,
                    'death_reason': safe_traverse_attrs(child, 'Child', 'DeathReason') or Undefined,
                    # 'diseases': child['NewbornSeakness'] or Undefined,
                })
            main_item['body']['kids'] = kids

        return entities

"""
      <ChildBirthData xmlns="https://68.r-mis.ru/esb/services/">
         <PatientId>5568693</PatientId>
         <Part1 description="general data">
            <InDate>2016-11-08+03:00</InDate>
            <ClinicId>490</ClinicId>
            <ChildBirth>
               <Date>2016-11-08+03:00</Date>
               <Time>00:00:00.000+03:00</Time>
               <PregnantWeeks>12</PregnantWeeks>
               <Diagnoses>
                  <MainDiagnos>7778</MainDiagnos>
                  <ComplicationDiagnoses>
                     <Diagnos>G00.0</Diagnos>
                  </ComplicationDiagnoses>
                  <ExtraDiagnoses>
                     <Diagnos>7778</Diagnos>
                  </ExtraDiagnoses>
               </Diagnoses>
               <ChildBirthOutcome>Роды</ChildBirthOutcome>
               <EmployeeId>90</EmployeeId>
            </ChildBirth>
            <OrgName/>
            <BirthSpeciality/>
            <AfterBirthSpeciality/>
            <HelpProvided/>
            <Abort/>
         </Part1>
         <Part2 description="mother death info">
            <MotherDeathData>
               <DeathDate>2016-11-17+03:00</DeathDate>
               <DeathTime xsi:nil="true"/>
               <MotherDeathReason xsi:nil="true"/>
               <PatologicalDiagnos>Тестовая запись 2</PatologicalDiagnos>
               <AcompanyDiagnos xsi:nil="true"/>
               <ComplicationDiagnos xsi:nil="true"/>
            </MotherDeathData>
            <LkkResult/>
         </Part2>
         <Part3 description="complications">
            <BirthWaterBreak/>
            <PrenatalWaterBreak/>
            <BirthPowerWeakness/>
            <AmiaticWater/>
            <PatologicPreliminaryPeriod/>
            <BirthActivityAnomaly/>
            <Horiamnionit/>
            <PerinealRupture/>
            <Nefropaty/>
            <Anemia/>
            <InfectionDuringBirth/>
            <InfectionAfterBirth/>
            <CordPatology/>
            <PlacentaPatology/>
         </Part3>
         <Part4 description="matnipulation"/>
         <Part5 description="surgery">
            <CesarianDelivery/>
            <Forceps/>
            <Vacuum/>
            <Indicator/>
            <Speciality/>
            <Anestesia/>
            <Hysterectomy/>
            <Complication/>
            <Embryotomy/>
         </Part5>
         <Part6 description="children info">
            <Child>
               <Alive>true</Alive>
               <Gender>2</Gender>
               <Weight>1200</Weight>
               <Height>55</Height>
               <BirthDate>2016-11-08+03:00</BirthDate>
               <BirthTime>00:00:00.000+03:00</BirthTime>
               <FullTerm>Доношенный</FullTerm>
               <Apgar_1min>4</Apgar_1min>
               <Apgar_5min>5</Apgar_5min>
               <Apgar_10min>5</Apgar_10min>
               <DeathDate xsi:nil="true"/>
               <DeathTime xsi:nil="true"/>
               <DeathReason xsi:nil="true"/>
               <NewbornSickness/>
            </Child>
            <Child>
               <Alive>true</Alive>
               <Gender>3</Gender>
               <Weight>780</Weight>
               <Height>50</Height>
               <BirthDate>2016-11-08+03:00</BirthDate>
               <BirthTime>00:00:00.000+03:00</BirthTime>
               <FullTerm>Доношенный</FullTerm>
               <Apgar_1min xsi:nil="true"/>
               <Apgar_5min xsi:nil="true"/>
               <Apgar_10min xsi:nil="true"/>
               <DeathDate>2016-11-17+03:00</DeathDate>
               <DeathTime xsi:nil="true"/>
               <DeathReason xsi:nil="true"/>
               <NewbornSickness/>
            </Child>
            <Child>
               <Alive>true</Alive>
               <Gender>3</Gender>
               <Weight>2580</Weight>
               <Height>53</Height>
               <BirthDate>2016-11-08+03:00</BirthDate>
               <BirthTime>00:00:00.000+03:00</BirthTime>
               <FullTerm>Доношенный</FullTerm>
               <Apgar_1min>5</Apgar_1min>
               <Apgar_5min>5</Apgar_5min>
               <Apgar_10min>8</Apgar_10min>
               <DeathDate xsi:nil="true"/>
               <DeathTime xsi:nil="true"/>
               <DeathReason xsi:nil="true"/>
               <NewbornSickness/>
            </Child>
            <Child>
               <Alive>false</Alive>
               <Gender>2</Gender>
               <Weight>4300</Weight>
               <Height>52</Height>
               <BirthDate>2016-11-08+03:00</BirthDate>
               <BirthTime>00:00:00.000+03:00</BirthTime>
               <FullTerm>Доношенный</FullTerm>
               <Apgar_1min>8</Apgar_1min>
               <Apgar_5min>8</Apgar_5min>
               <Apgar_10min>10</Apgar_10min>
               <DeathDate>2016-11-08+03:00</DeathDate>
               <DeathTime>00:00:00.000+03:00</DeathTime>
               <DeathReason xsi:nil="true"/>
               <NewbornSickness/>
            </Child>
            <Child>
               <Alive>true</Alive>
               <Gender>3</Gender>
               <Weight>6000</Weight>
               <Height>56</Height>
               <BirthDate>2016-11-08+03:00</BirthDate>
               <BirthTime>00:00:00.000+03:00</BirthTime>
               <FullTerm>Доношенный</FullTerm>
               <Apgar_1min xsi:nil="true"/>
               <Apgar_5min xsi:nil="true"/>
               <Apgar_10min xsi:nil="true"/>
               <DeathDate>2016-11-17+03:00</DeathDate>
               <DeathTime xsi:nil="true"/>
               <DeathReason xsi:nil="true"/>
               <NewbornSickness/>
            </Child>
         </Part6>
      </ChildBirthData>
"""