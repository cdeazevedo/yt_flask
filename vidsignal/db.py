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