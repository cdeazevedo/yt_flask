from flask import (
    Blueprint, g, render_template, g, jsonify
)

from vidsignal.db import get_channels, get_channel_videos, get_realtime_videos

import pandas as pd

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
def dashboard():
    # This route is going to pull a bunch of data? Let's start with a list of 
    # channels
    # See if user is logged in or in guest mode
    if g.user:
        logged_in=True
    else:
        logged_in=False
    # get some data dictionary ready
    data = {}
    # Get channel list
    data['channels'] = get_channels()
    
    return render_template('dashboard/dashboard.html', 
                           data=data,
                           logged_in=logged_in,
                           user=g.user)

@bp.route('/dashboard/<selected_channel_id>')
def dashboard_for_channel(selected_channel_id):
    channel_data = {}
    channel_data['videos'] = get_channel_videos(selected_channel_id)
    channel_data['realtime'] = get_realtime_videos(selected_channel_id)
    #print(channel_data)
    #print(selected_channel_id)
    return jsonify(channel_data)