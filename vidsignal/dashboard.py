from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, g
)

from vidsignal.db import get_db
from vidsignal.auth import login_required

import json
import plotly
import plotly.express as px
import pandas as pd

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
def dashboard():
    if g.user:
        logged_in=True
    else:
        logged_in=False
    df = pd.DataFrame({
        'Fruit': ['Apples', 'Oranges', 'Bananas', 'Apples', 'Oranges', 'Bananas'],
        'Amount': [4, 1, 2, 2, 4, 5],
        'City': ['SF', 'SF', 'SF', 'Montreal', 'Montreal', 'Montreal']
    })
    color_mapping = {
    'SF': 'blue',  # You can use any valid CSS color here
    'Montreal': 'red',
    # Add more cities and colors as needed
    }
    df['Color'] = df['City'].map(color_mapping)
    return render_template('dashboard/dashboard.html', 
                           data=df.to_dict(orient='records'),
                           logged_in=logged_in)

