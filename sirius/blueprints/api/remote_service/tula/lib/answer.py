#! coding:utf-8
"""


@author: BARS Group
@date: 26.09.2016

"""
from sirius.blueprints.api.remote_service.lib.answer import RemoteAnswer
import xml.etree.ElementTree as ET


class TulaAnswer(RemoteAnswer):
    def xml_to_dict(self, result):
        e = ET.XML(result.content)
        return e
