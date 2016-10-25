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


@module.route('/api/send/remote/', methods=["POST"])
@local_api_method(hook=hook)
def api_send_remote():
    data = request.get_json()
    msg = Message(data)
    msg.to_remote_service()
    msg.set_send_event_type()
    prod = LocalProducer()
    res = prod.send(msg)
    return res
