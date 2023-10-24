import os
from flask import Flask, render_template, g

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )
    
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
        
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
       
    @app.route('/')
    def index():
        if g.user:
            logged_in = True
        else:
            logged_in = False
        return render_template('index.html', logged_in=logged_in)
    
    from . import db
    db.init_app(app)
    
    from . import auth
    app.register_blueprint(auth.bp)
    
    from . import dashboard
    app.register_blueprint(dashboard.bp)
        
    return app