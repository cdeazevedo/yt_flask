from flask import Flask, render_template, request
import mysql.connector
from config import create_db_connection, YT_API_KEY
import requests
from googleapiclient.discovery import build

youtube_service = build('youtube','v3', developerKey=YT_API_KEY)

application = Flask(__name__)

@application.route('/')
def index():
    return render_template("index.html")

@application.route('/search', methods=['GET', 'POST'])
def search_channel():
    if request.method == "POST":
        channel_query = request.form['channel_query']
        
        if not channel_query:
            return "Please enter a channel name or ID."
        
        search_response = youtube_service.search().list(
            q=channel_query,
            type='channel',
            part='id,snippet'
        ).execute()
        
        # Check response for channels
        if 'items' in search_response:
            channel_info = search_response['items'][0]
            
            channel_id = channel_info['id']['channelId']
            name = channel_info['snippet']['title']
            thumbnail_uri = channel_info['snippet']['thumbnails']['default']['url']
                    
            return render_template('search_channel.html', channel_found=True, 
                                   channel_id=channel_id, channel_name=name,
                                   thumbnail_uri=thumbnail_uri)
        else: 
            return render_template('search_channel.html', channel_found=False)
    else:
        # Handle GET request to display the search form
        return render_template('search_channel.html', channel_found=False)

@application.route('/confirm', methods=['POST'])
def confirm_track():
    channel_id = request.form['channel_id']
    channel_name = request.form['channel_name']
    thumbnail_uri = request.form['thumbnail_uri']
    sql_query_save = """
    INSERT INTO channels(channel_id, name, thumbnail_uri)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE name = VALUES(name), thumbnail_uri = VALUES(thumbnail_uri);
    """
    connection = create_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query_save, (channel_id, channel_name, thumbnail_uri))
            connection.commit()
        print("Channel Saved")
    except mysql.connector.Error as err:
        print("Error: ", err)
        
    finally:
        connection.close()
    return f"Now tracking: {channel_name} (channel id: {channel_id})."

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
            '''
            
    
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
            
            thumbnail_sql_query = '''
            SELECT thumbnail_uri FROM
            channels WHERE channel_id = %s
            '''
            cursor.execute(thumbnail_sql_query, (channel_id,))
            thumbnail_url = cursor.fetchall()[0][0]
            
    except mysql.connector.Error as err:
        print("Error: ", err)
        # Handle the error, e.g., return an error message or an empty list

    finally:
        connection.close()
    
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