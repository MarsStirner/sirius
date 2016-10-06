#! coding:utf-8
"""


@author: BARS Group
@date: 06.10.2016

"""

import sys
import os
import runpy
path = os.path.dirname(sys.modules[__name__].__file__)
path = os.path.join(path, '..')
sys.path.insert(0, path)
runpy.run_module('flask', run_name="__main__",alter_sys=True)
