from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from vidsignal.db import get_db
from vidsignal.auth import login_required

import plotly.express as px

bp = Blueprint('dashboard', __name__)

@bp.route('/guest')
def guest():
    return render_template('dashboard/guest.html')

@bp.route('/user')
@login_required
def user():
    fig = px.line(x=[1, 2, 3, 4], y=[10, 11, 9, 12])

    # Convert the figure to JSON
    graph_json = fig.to_json()

    return render_template('dashboard/user.html', graph_json=graph_json)