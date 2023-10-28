import os
from flask import Flask, render_template, g

def create_app(test_config=None):
    application = Flask(__name__, instance_relative_config=True)
    application.config.from_mapping(
        SECRET_KEY='dev'
    )
    
    if test_config is None:
        application.config.from_pyfile('config.py', silent=True)
    else:
        application.config.from_mapping(test_config)
        
    try:
        os.makedirs(application.instance_path)
    except OSError:
        pass
       
    @application.route('/')
    def index():
        if g.user:
            logged_in = True
        else:
            logged_in = False
        return render_template('index.html', logged_in=logged_in)
    
    from . import db
    db.init_app(application)
    
    from . import auth
    application.register_blueprint(auth.bp)
    
    from . import dashboard
    application.register_blueprint(dashboard.bp)
        
    return application