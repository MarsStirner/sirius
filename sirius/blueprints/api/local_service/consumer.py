#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.api.local_service.risar.active.request import request_by_url
from sirius.blueprints.monitor.exception import InternalError
from sirius.lib.implement import Implementation
from sirius.lib.message import Message
from sirius.blueprints.api.local_service.producer import LocalProducer


class LocalConsumer(object):
    def process(self, msg):
        assert isinstance(msg, Message)
        res = None
        hdr = msg.get_header()
        # сценарий обработки сообщения
        if msg.is_request:
            parser, answer = request_by_url(hdr.method, hdr.url, msg.get_data())
            local_data = parser.get_data(answer)

            next_msg = Message(local_data)
            next_msg.to_remote_service()
            next_msg.set_send_data_type()
            next_msg.get_header().meta.update(hdr.meta)

            if msg.is_immediate_answer:
                res = next_msg
            else:
                prod = LocalProducer()
                prod.send(next_msg)
        elif msg.is_result:
            parser, answer = request_by_url(hdr.method, hdr.url, msg.get_data())
            req_res = parser.get_data(answer)
        elif msg.is_send_data:
            implement = Implementation()
            rmt_sys_code = msg.get_header().meta['remote_system_code']
            reformer = implement.get_reformer(rmt_sys_code)
            entities = reformer.reform_msg(msg)
            reformer.send_to_local_data(entities, request_by_url)
        else:
            raise InternalError('Message has not type')

        return res
