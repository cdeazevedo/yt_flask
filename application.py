from flask import Flask, render_template, request, jsonify
import mysql.connector
from config import create_db_connection, YT_API_KEY
import requests



application = Flask(__name__)

@application.route('/')
def index():
    return render_template("index.html")

@application.route('/channels')
def channels():
    connection = create_db_connection()
    channel_data = []

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT channel_id, name from channels')
            channel_data = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error: ", err)

    finally:
        connection.close()

    # Preprocess the data into a list of dictionaries
    channels = [{'channel_id': row[0], 'channel_name': row[1]} for row in channel_data]

    return render_template("channels.html", channels=channels)

@application.route('/get_channel_data/<channel_id>')
def get_channel_data(channel_id):
    connection = create_db_connection()
    
    try:
        with connection.cursor() as cursor:
            # SQL Query
            sql_query = '''
            SELECT v.title, FORMAT(vv.views, 0), v.duration, DATE_FORMAT(v.published_date, '%d-%b-%Y') as formatted_date, v.video_id
            FROM videos as v 
            LEFT JOIN video_views as vv on v.video_id = vv.video_id
            WHERE v.channel_id = %s
            AND vv.timestamp = (
                SELECT MAX(timestamp) FROM video_views
                WHERE video_id = v.video_id
            )
            ORDER BY vv.views DESC
            LIMIT 10
            '''
            
            #cursor.execute('SELECT title, views, duration, published_date FROM videos WHERE v.channel_id = %s LIMIT 15', (channel_id,))
            cursor.execute(sql_query, (channel_id,))
            channel_data = cursor.fetchall()
          
            views_sql_query = '''
            SELECT FORMAT(SUM(vv.views), 0)
            FROM videos as v 
            LEFT JOIN video_views as vv on v.video_id = vv.video_id
            WHERE v.channel_id = %s
            AND vv.timestamp = (
                SELECT MAX(timestamp) FROM video_views
                WHERE video_id = v.video_id
            )
            ORDER BY vv.views DESC
            '''
            
            cursor.execute(views_sql_query, (channel_id,))
            total_views = cursor.fetchall()[0][0]
            
    except mysql.connector.Error as err:
        print("Error: ", err)
        # Handle the error, e.g., return an error message or an empty list

    finally:
        connection.close()

    # Get Profile pic URL
    thumbnail_request_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet&id={channel_id}&fields=items%2Fsnippet%2Fthumbnails&key={YT_API_KEY}" 
    response = requests.get(thumbnail_request_url)
    if response.status_code == 200:
        thumbnail_url = response.json()['items'][0]['snippet']['thumbnails']['default']['url']
        print(thumbnail_url)
    else:
        thumbnail_url = None  # Set to None if there's an error or no URL

    # Check if there is data available
    if channel_data:
        return render_template(
            "channel_data.html",
            thumbnail_url=thumbnail_url,
            channel_data=channel_data,
            total_views=total_views
        )
    else:
        # If no data is available, return a message or an empty response
        return "No data available for this channel."

@application.route("/db_test", methods=['GET', 'POST'])
def db_test():
    if request.method == 'POST':
        try:
            # Attempt to establish a database connection
            db_connection = create_db_connection()
            db_connection.close()
            result = "Database connection successful!"
        except mysql.connector.Error as err:
            result = f"Database connection error: {err}"
    else:
        result = None  # No result initially for GET requests

    return render_template("test.html", result=result)

if __name__ == "__main__":
    application.run(debug=True)