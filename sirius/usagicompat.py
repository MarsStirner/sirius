# -*- coding: utf-8 -*-
import os
from flask.helpers import get_debug_flag

from tsukino_usagi.client import TsukinoUsagiClient
from version import version as app_version


class BIUsagiClient(TsukinoUsagiClient):
    fl_app = None

    def __init__(self, app, *a, **kw):
        super(BIUsagiClient, self).__init__(*a, **kw)
        self.fl_app = app

    def on_configuration(self, configuration):
        configuration['APP_VERSION'] = app_version
        is_debug = get_debug_flag()
        is_server = configuration['SERVER']
        is_autotest = os.environ.get('TESTING') == '1'
        if is_debug:
            if is_server:
                if is_autotest:
                    env_conf_name = 'test_autotest'
                else:
                    env_conf_name = 'test'
            else:
                if is_autotest:
                    env_conf_name = 'dev_autotest'
                else:
                    env_conf_name = 'dev'
        else:
            env_conf_name = 'prod'

        env_conf = configuration.get(env_conf_name, {})
        configuration.update(env_conf)
        self.fl_app.config.update(configuration)
