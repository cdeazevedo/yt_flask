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
    # Fetch column names from the cursor description
    column_names = [desc[0] for desc in crsr.description]
    # Convert the list of tuples to a list of dictionaries
    channel_list = [dict(zip(column_names, row)) for row in channels]
    return channel_list

def get_channel_videos(channel_id):
    db = create_db_connection()
    cursor = db.cursor()
    sql_query='''
    SELECT v.video_id, v.title, v.duration, v.published_date, vv.views
    FROM videos v
    LEFT JOIN video_views vv ON v.video_id = vv.video_id
    WHERE v.channel_id = %s AND vv.views > 0
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
    column_names = [desc[0] for desc in crsr.description]
    video_list = [dict(zip(column_names, row)) for row in videos]
    return video_list

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
    column_names = [desc[0] for desc in crsr.description]
    video_list = [dict(zip(column_names, row)) for row in videos]
    return video_list

def get_average_views_per_year(channel_id):
    db = create_db_connection()
    cursor = db.cursor()
    sql_query='''        
        SELECT YEAR(v.published_date) AS publication_year, AVG(vv.views) AS average_views
        FROM videos v
        LEFT JOIN video_views vv ON v.video_id = vv.video_id
        WHERE v.channel_id = %s
        AND vv.timestamp = (
            SELECT MAX(timestamp) FROM video_views 
            WHERE video_id = v.video_id
        )
        GROUP BY YEAR(v.published_date)
        '''
    with cursor as crsr:
        crsr.execute(sql_query, (channel_id,))
        videos = crsr.fetchall()
        crsr.close()
    column_names = [desc[0] for desc in cursor.description]
    video_list = [dict(zip(column_names, row)) for row in videos]
    return video_list