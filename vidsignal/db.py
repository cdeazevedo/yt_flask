from flask import current_app, g
from config import create_db_connection

def get_db():
    if 'db' not in g:
        g.db = create_db_connection()
    
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()
        
def  init_app(app):
    app.teardown_appcontext(close_db)
    
def get_channels():
    db = create_db_connection()
    cursor = db.cursor()
    sql_query = '''
    SELECT channel_id, name, thumbnail_uri, published_date
    FROM channels 
    ORDER BY name
    '''
    with cursor as crsr:
        crsr.execute(sql_query)
        channels = crsr.fetchall()
        crsr.close()
    # convert to list that's easier to deal with later
    channel_list = []
    for channel in channels:
        channel_dict = {
            'channel_id':channel[0],
            'channel_name':channel[1],
            'channel_image':channel[2],
            'published_date':channel[3]
        }
        channel_list.append(channel_dict)
    
    return channel_list

def get_channel_videos(channel_id):
    db = create_db_connection()
    cursor = db.cursor()
    sql_query='''
    SELECT v.video_id, v.title, v.duration, v.published_date, vv.views
    FROM videos v
    LEFT JOIN video_views vv ON v.video_id = vv.video_id
    WHERE v.channel_id = %s
    AND vv.timestamp = (
                SELECT MAX(timestamp) FROM video_views
                WHERE video_id = v.video_id
            )
    ORDER BY vv.views DESC
    '''
    with cursor as crsr:
        crsr.execute(sql_query, (channel_id,))
        videos = crsr.fetchall()
        crsr.close()
    return videos

def get_realtime_videos(channel_id):
    """Return a list of videos for a channel to calculate realtime performance."""
    db = create_db_connection()
    cursor = db.cursor()
    sql_query='''
    SELECT v.video_id, v.title, v.duration, v.published_date, vv.views, vv.timestamp
    FROM videos v
    LEFT JOIN video_views vv ON v.video_id = vv.video_id
    WHERE v.channel_id = %s
    ORDER BY v.video_id, vv.timestamp DESC
    '''
    with cursor as crsr:
        crsr.execute(sql_query, (channel_id,))
        videos = crsr.fetchall()
        crsr.close()
    return videos

