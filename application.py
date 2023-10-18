from flask import Flask, render_template, request
import mysql.connector
from config import create_db_connection, YT_API_KEY
from googleapiclient.discovery import build
import datetime
import pandas as pd

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
    except mysql.connector.Error as err:
        print("Error: ", err)
        
    finally:
        connection.close()
    return f"Now tracking: {channel_name} (channel id: {channel_id}). <br/> <a href='/search'>Back</a>"

@application.route('/channels')
def channels():
    connection = create_db_connection()
    channel_data = []

    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT channel_id, name from channels ORDER BY name')
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
            SELECT 
                v.title,
                FORMAT(vv.views, 0),
                v.duration, 
                ROUND((vv.views / SUM(vv.views) OVER ()) * 100, 1) AS percent_of_total_views,
                DATE_FORMAT(v.published_date, '%d-%b-%Y') as formatted_date, 
                v.video_id, 
                v.published_date
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
            total_videos = len(channel_data)

            views_sql_query = '''
            SELECT SUM(vv.views)
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
            if total_views:
                average_views_per_video = int(total_views // total_videos)
            
                #Format values for prettiness
                total_views = '{:,}'.format(total_views)
                average_views_per_video = '{:,}'.format(average_views_per_video)
                total_videos = '{:,}'.format(total_videos)
            
            thumbnail_sql_query = '''
            SELECT thumbnail_uri FROM
            channels WHERE channel_id = %s  
            '''
            cursor.execute(thumbnail_sql_query, (channel_id,))
            thumbnail_url = cursor.fetchall()[0][0]
            
            
            # Set date range
            seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')
            
            ## Get data for realtime views 
            realtime_sql_query = '''
            SELECT v.title, vv.views, v.duration, DATE_FORMAT(v.published_date, '%d-%b-%Y') as formatted_date, v.video_id, v.published_date, vv.timestamp
            FROM videos as v 
            LEFT JOIN video_views as vv on v.video_id = vv.video_id
            WHERE v.channel_id = %s
            AND vv.timestamp >= %s
            ORDER BY v.video_id, vv.timestamp 
            '''
            
            cursor.execute(realtime_sql_query, (channel_id, seven_days_ago_str))
            realtime_data = cursor.fetchall()
    
            df = pd.DataFrame(realtime_data, 
                              columns=['title', 'views', 'duration', 
                                       'formatted_published_date', 'video_id', 
                                       'published_date', 'timestamp'])
            
            df['change_in_views'] = df.groupby('video_id')['views'].diff()
            df['change_in_timestamp'] = df.groupby('video_id')['timestamp'].diff()
            df.dropna(inplace=True)
            df['change_in_timestamp_hours'] = df['change_in_timestamp'].dt.total_seconds() / 3600
            grouped = df.groupby('video_id', ).agg({
                'change_in_views' : 'sum',
                'change_in_timestamp_hours' : 'sum',
                'title': 'first',  
                'published_date': 'first'  
            }).reset_index()
            # Calculate real-time (48 hour) view estimate
            grouped['change_in_views_per_hour'] = grouped['change_in_views'] / grouped['change_in_timestamp_hours']
            grouped['realtime_views_estimate']  = grouped['change_in_views_per_hour'] * 48
            grouped.sort_values('realtime_views_estimate', inplace=True, ascending=False)
            realtime_df = grouped[['video_id', 'title', 'published_date', 'realtime_views_estimate']]
            realtime_total = '{:,}'.format(round(realtime_df['realtime_views_estimate'].sum(),0))
            realtime_df_as_dict = realtime_df.to_dict(orient='records')
            #print(realtime_df_as_dict[0])
            for item in realtime_df_as_dict:
                item['realtime_views_estimate'] = '{:,}'.format(round(item['realtime_views_estimate'],0))
            ## recent uploads
            recent_data = sorted(channel_data, key=lambda x: x[6], reverse=True)
            
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
            total_views=total_views,
            total_videos=total_videos,
            average_views_per_video=average_views_per_video,
            recent_data=recent_data,
            realtime_df_as_dict = realtime_df_as_dict,
            realtime_total = realtime_total
        )
    else:
        # If no data is available, return a message or an empty response
        return "No data available for this channel. Try again later."

if __name__ == "__main__":
    application.run(debug=True)