# -*- coding: utf-8 -*-
"""Test configs."""
import os
from sirius.app import create_sirius_app


def test_production_config():
    """Production config."""
    testing = os.environ.get('TESTING')
    debug = os.environ.get('FLASK_DEBUG')
    os.environ['TESTING'] = '0'
    os.environ['FLASK_DEBUG'] = '0'
    app = create_sirius_app()
    os.environ['TESTING'] = testing
    os.environ['FLASK_DEBUG'] = debug
    assert app.config['ENV'] == 'prod'
    assert app.config['DEBUG'] is False
    assert app.config['DEBUG_TB_ENABLED'] is False
    assert app.config['ASSETS_DEBUG'] is False


def test_dev_config():
    """Development config."""
    testing = os.environ.get('TESTING')
    debug = os.environ.get('FLASK_DEBUG')
    os.environ['TESTING'] = '0'
    os.environ['FLASK_DEBUG'] = '1'
    app = create_sirius_app()
    os.environ['TESTING'] = testing
    os.environ['FLASK_DEBUG'] = debug
    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG'] is True
    assert app.config['ASSETS_DEBUG'] is True
