#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer


class TambovAnswer(RemoteAnswer):

    def process(self, result):
        return self.xml_to_dict(result)

    def xml_to_dict(self, data):
        # todo:
        return data
