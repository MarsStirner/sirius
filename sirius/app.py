# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import os
from hitsl_utils.wm_api import WebMisJsonEncoder
from sirius.usagicompat import BIUsagiClient
from flask import Flask, render_template

from sirius import commands
from sirius.assets import assets
from sirius.extensions import bcrypt, cache, csrf_protect, db, debug_toolbar, login_manager, migrate, celery

app = Flask(__name__)


def create_sirius_app():
    return init_sirius_app(BIUsagiClient, True)


def init_sirius_app(usagi_client, new_app=False, is_lazy_db=False):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param usagi_client: configuration client.
    :param new_app: The configuration object to use.
    """
    ini_app = Flask(__name__) if new_app else app

    conf_url = os.getenv('TSUKINO_USAGI_URL')
    usagi = usagi_client(ini_app, ini_app.wsgi_app, conf_url, 'sirius')
    ini_app.wsgi_app = usagi.app
    usagi()

    # ini_app.json_encoder = WebMisJsonEncoder

    register_extensions(ini_app, is_lazy_db)
    register_blueprints(ini_app)
    register_errorhandlers(ini_app)
    register_shellcontext(ini_app)
    register_commands(ini_app)
    init_logger()
    return ini_app


def register_extensions(app, is_lazy_db):
    """Register Flask extensions."""
    assets.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    if not is_lazy_db:
        db.init_app(app)
    # csrf_protect.init_app(app)
    # principal.init_app(app)
    # beaker_session.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    if app.config['CELERY_ENABLED']:
        celery.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    from sirius.models.system import RegionCode
    from sirius.blueprints import public, user, reformer, scheduler, api
    app.register_blueprint(public.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(scheduler.app.module)
    app.register_blueprint(reformer.app.module)
    app.register_blueprint(api.local_service.risar.app.module)
    if app.config['REGION_CODE'] == RegionCode.TULA:
        app.register_blueprint(api.remote_service.tula.app.module)
    elif app.config['REGION_CODE'] == RegionCode.TAMBOV:
        app.register_blueprint(api.remote_service.tambov.app.module)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    from sirius.blueprints import public, user

    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    # app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def init_logger():
    app_version = app.config.get('APP_VERSION', 'Unversioned App')
    import logging
    from pysimplelogs2 import SimplelogHandler

    logger = logging.getLogger('simple')
    if logger.handlers:
        # на каждый тестовый блок переинициализация
        # исключаем дубли хэндлеров
        return

    debug_mode = app.config['DEBUG']

    formatter = logging.Formatter(
        u'%(asctime)s - %(pathname)s:%(funcName)s [%(levelname)s] %(message)s'
        if debug_mode else
        u'%(message)s'
    )

    handler = SimplelogHandler()
    url = app.config['SIMPLELOGS_URL']
    handler.set_url(url)
    handler.owner = {
        'name': app.config['PROJECT_NAME'],
        'version': u'%s' % (app_version,)
    }
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())

    logger.debug('SimpleLogs Handler initialized')
