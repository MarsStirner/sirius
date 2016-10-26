#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.local_service.risar.app import module
from sirius.blueprints.api.local_service.risar.lib.parser import RequestLocalData
from sirius.blueprints.api.local_service.producer import LocalProducer
from sirius.blueprints.monitor.exception import local_api_method
from sirius.lib.message import Message
from flask import request
from sirius.blueprints.monitor.logformat import hook
from sirius.models.operation import OperationCode


@module.route('/api/request/local/', methods=["POST"])
@local_api_method(hook=hook)
def api_request_local():
    data = request.get_json()
    rld = RequestLocalData(data)
    msg = Message(None)
    msg.to_local_service()
    msg.set_request_type()
    msg.set_method(rld.method, rld.url)
    prod = LocalProducer()
    res = prod.send(msg)
    return res


@module.route('/api/request/remote/', methods=["POST"])
@local_api_method(hook=hook)
def api_request_remote():
    # запрос данных из удаленной системы по ID удаленной системы
    # если коды внешней системы и шины разъедутся, придется мапить
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


@module.route('/api/send/event/remote/', methods=["POST"])
@local_api_method(hook=hook)
def api_send_event_remote():
    data = request.get_json()
    msg = Message(data)
    msg.to_remote_service()
    msg.set_send_event_type()
    prod = LocalProducer()
    res = prod.send(msg)
    return res
