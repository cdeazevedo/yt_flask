from flask import (
    Blueprint, g, render_template, g, jsonify
)

from vidsignal.db import get_channels, get_channel_videos, get_realtime_videos
import pandas as pd

bp = Blueprint('dashboard', __name__)

def process_realtime_data(video_list):
    """Take the results of the realtime video query from SQL and turn into measure of new views on each video"""
    df = pd.DataFrame(video_list)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['video_id', 'timestamp'])
    # Calculate the new views and time elapsed for each video
    df['new_views'] = df.groupby('video_id')['views'].diff()
    df['time_elapsed'] = df.groupby('video_id')['timestamp'].diff().dt.total_seconds()
    # drop NA
    df = df.dropna()
    # convert to daily views
    df['views_per_day'] = df['new_views'] / (df['time_elapsed'] / (60 * 60 *24))
    top_10_videos = df.groupby('video_id').agg({
        'views_per_day': 'mean',
        'title': 'first',
        'published_date': 'first'
    }).nlargest(10, 'views_per_day').reset_index()
    data = df.to_dict(orient='records')
    top_10_videos = top_10_videos.to_dict(orient='records')
    return data, top_10_videos

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
    realtime_data, top_10_vides = process_realtime_data(get_realtime_videos(selected_channel_id))
    channel_data['realtime'] = realtime_data
    channel_data['top_10_videos'] = top_10_vides
    #print(channel_data)
    #print(selected_channel_id)
    return jsonify(channel_data)