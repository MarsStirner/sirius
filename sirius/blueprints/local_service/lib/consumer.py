#! coding:utf-8
"""


@author: BARS Group
@date: 23.09.2016

"""
from sirius.blueprints.local_service.lib.client.request import request_by_url
from sirius.lib.message import Message
from sirius.blueprints.local_service.lib.producer import LocalProducer


class LocalConsumer(object):
    def process(self, msg):
        assert isinstance(msg, Message)
        res = None
        hdr = msg.get_header()
        # сценарий обработки сообщения
        if msg.is_request:
            local_data = request_by_url(hdr.method, hdr.url, msg.get_data())

            next_msg = Message(local_data)
            next_msg.to_remote_service()
            next_msg.set_send_data_type()
            next_msg.set_method(hdr.method, hdr.url)

            if msg.is_immediate_answer:
                res = next_msg
            else:
                prod = LocalProducer()
                prod.send(next_msg)
        elif msg.is_result:
            req_res = request_by_url(hdr.method, hdr.url, msg.get_data())
        elif msg.is_send_data:
            local_data = request_by_url(hdr.method, hdr.url, msg.get_data())
            remote_data = msg.get_source_data()

            next_msg = Message(local_data)
            next_msg.to_remote_service()
            next_msg.set_result_type()
            next_msg.set_source_data(remote_data)
            prod = LocalProducer()
            prod.send(next_msg)
        else:
            raise Exception('Message has not type')

        return res
