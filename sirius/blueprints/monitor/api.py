#! coding:utf-8
"""
Функции сбора данных сообщения/пакета/элемента и сохранения в БД/логи

@author: BARS Group
@date: 21.10.2016

"""
from abc import ABCMeta, abstractmethod


class IStreamMeta(object):
    # todo: когда пакеты перейдут в классы, эти данные будут приходить от объектов собщений
    __metaclass__ = ABCMeta

    @classmethod
    @abstractmethod
    def get_stream_meta(cls, obj):
        pass
