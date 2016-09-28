# -*- coding: utf-8 -*-
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
        is_dev = get_debug_flag()
        env_conf_name = 'dev' if is_dev else 'prod'

        env_conf = configuration.get(env_conf_name, {})
        configuration.update(env_conf)
        self.fl_app.config.update(configuration)
