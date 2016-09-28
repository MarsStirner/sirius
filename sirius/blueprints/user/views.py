# -*- coding: utf-8 -*-
"""User views."""
from flask import Blueprint, render_template
from flask_login import login_required

blueprint = Blueprint('user', __name__, url_prefix='/users', template_folder='templates', static_folder='static')


@blueprint.route('/')
@login_required
def members():
    """List members."""
    return render_template('user/members.html')
