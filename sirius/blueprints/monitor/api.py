#! coding:utf-8
"""
Функции сбора данных сообщения/пакета/элемента и сохранения в БД/логи

@author: BARS Group
@date: 21.10.2016

"""
from abc import ABCMeta, abstractmethod


class IStreamMeta(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_stream_meta(self):
        pass

    @abstractmethod
    def get_stream_body(self):
        pass
