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
    sql_query = '''SELECT * FROM channels ORDER BY name'''
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
            'channel_image':channel[2]
        }
        channel_list.append(channel_dict)
    
    return channel_list

def get_channel_data(channel_id):
    db = create_db_connection()
    cursor = db.cursor()
    sql_query='SELECT * FROM videos for channel_id = %s'
    with cursor as crsr:
        crsr.execute(sql_query, (channel_id))
        channel_data = crsr.fetchall()
        crsr.close()
    return channel_data