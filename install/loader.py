# -*- coding: utf-8 -*-
import copy
import os

import yaml

__author__ = 'viruzzz-kun'


class ConfigLoader(yaml.Loader):
    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(ConfigLoader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, ConfigLoader)

    def inherit(self, node):
        kwds = self.construct_mapping(node)

        yield kwds

        ancestors = kwds.pop('ancestors', [])
        updater = copy.copy(kwds)
        for ancestor in ancestors:
            kwds.update(copy.deepcopy(ancestor))
        kwds.update(updater)

    def readfile(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return f.read()


ConfigLoader.add_constructor('!include', ConfigLoader.include)
ConfigLoader.add_constructor('!inherit', ConfigLoader.inherit)
ConfigLoader.add_constructor('!readfile', ConfigLoader.readfile)
