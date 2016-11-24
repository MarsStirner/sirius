#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.app import app
from sirius.blueprints.api.local_service.risar.app import module
from sirius.blueprints.api.local_service.risar.entities import RisarEntityCode
from sirius.blueprints.api.local_service.risar.events import RisarEvents
from sirius.blueprints.api.local_service.risar.lib.parser import RequestLocalData
from sirius.blueprints.api.local_service.producer import LocalProducer
from sirius.blueprints.monitor.exception import local_api_method
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from flask import request
from sirius.blueprints.monitor.logformat import hook
from sirius.models.operation import OperationCode
from sirius.models.system import RegionCode


@module.route('/api/request/local/', methods=["POST"])
@local_api_method(hook=hook)
def api_request_local():
    data = request.get_json()
    rld = RequestLocalData(data)
    msg = Message(None)
    msg.to_local_service()
    msg.set_request_type()
    msg.set_method(rld.request_method, rld.request_url)
    msg.get_header().meta.update(rld.get_msg_meta())
    prod = LocalProducer()
    res = prod.send(msg)
    return res


@module.route('/api/request/remote/', methods=["POST"])
@local_api_method(hook=hook)
def api_request_remote():
    # запрос данных из удаленной системы по ID удаленной системы
    # если коды внешней системы и шины разъедутся, придется вынести RisarEntityCode
    data = request.get_json()
    rld = RequestLocalData(data)
    msg = Message(None)
    msg.to_remote_service()
    msg.set_request_type()
    meta = msg.get_header().meta
    meta['local_operation_code'] = OperationCode.READ_ONE
    meta['remote_system_code'] = rld.data.get('remote_system_code')
    meta['remote_entity_code'] = rld.data.get('remote_entity_code')
    meta['remote_main_id'] = rld.data.get('remote_main_id')
    prod = LocalProducer()
    res = prod.send(msg)
    return res


# todo: переделать event на immediate, т.к. передаются данные
@module.route('/api/send/event/remote/', methods=["POST"])
@local_api_method(hook=hook)
def api_send_event_remote():
    data = request.get_json()
    rld = RequestLocalData(data)
    msg = Message(rld.body)
    msg.to_remote_service()
    msg.set_send_event_type()
    msg.get_header().meta.update(rld.get_msg_meta())
    prod = LocalProducer()
    res = prod.send(msg)
    return res


@module.route('/api/client/local_id/', methods=["GET"])
@local_api_method(hook=hook)
def api_client_local_id():
    data = request.get_json()
    rld = RequestLocalData(data)
    implement = Implementation()
    reformer = implement.get_reformer(rld.data.get('remote_system_code'))
    local_id = reformer.get_local_id_by_remote(
        RisarEntityCode.CLIENT,
        rld.data.get('remote_entity_code'),
        rld.data.get('remote_main_id'),
    )
    return local_id


@module.route('/api/card/register/', methods=["POST"])
@local_api_method(hook=hook)
def api_card_register():
    data = request.get_json()
    rld = RequestLocalData(data)
    implement = Implementation()
    reformer = implement.get_reformer(rld.data.get('remote_system_code'))
    res = reformer.get_register_entity_match(
        RisarEntityCode.CARD,
        rld.data.get('local_main_id'),
        rld.data.get('remote_entity_code'),
        rld.data.get('remote_main_id'),
    )
    return res


@module.route('/api/events/binded/', methods=["GET"])
@local_api_method(hook=hook)
def api_events_binded():
    region_code = app.config.get('REGION_CODE')
    # todo: возможно вынести в БД
    bind_map = {
        RegionCode.TULA: [
            RisarEvents.CREATE_CARD,
            RisarEvents.MAKE_APPOINTMENT,
            RisarEvents.SAVE_CHECKUP,
            RisarEvents.CLOSE_CARD,
        ],
        RegionCode.TAMBOV: [
            RisarEvents.SAVE_CHECKUP,
            RisarEvents.ENTER_MIS_EMPLOYEE,
        ],
    }
    res = bind_map[region_code]
    return res
