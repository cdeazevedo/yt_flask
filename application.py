from flask import Flask, render_template, request, jsonify
import mysql.connector
from config import create_db_connection

application = Flask(__name__)

@application.route('/')
def index():
    return render_template("index.html")

@application.route('/channels')
def channels():
    connection = create_db_connection()
    channel_names = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT channel_id, name from channels')
            channel_data = cursor.fetchall()
            
    except mysql.connector.Error as err:
        print("Error: ", err)
        
    finally:
        connection.close()
        
    channel_ids = [row[0] for row in channel_data]
    channel_names = [row[1] for row in channel_data]
        
    return render_template("channels.html", channel_ids=channel_ids,channel_names=channel_names)

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
            
    except mysql.connector.Error as err:
        print("Error: ", err)
        # Handle the error, e.g., return an error message or an empty list

    finally:
        connection.close()

    # Check if there is data available
    if channel_data:
        # You can format the data as needed, for example, as a list of dictionaries
        formatted_data = [
            {
                "title": row[0],
                "views": row[1],
                "duration": row[2],
                "published_date": row[3],
                "video_id": row[4]
            }
            for row in channel_data
        ]
        # Return the data as JSON
        return jsonify(formatted_data)
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