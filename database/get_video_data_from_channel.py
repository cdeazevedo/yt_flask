import sys
from datetime import datetime
import googleapiclient.discovery
import googleapiclient.errors
from config import create_db_connection, YT_API_KEY
from utilities.get_related import (
    getChannelData,
    getPlaylistIds,
    getVideoIdsFrom,
    getVideoStatistics,
    videoTitle,
    viewCount,
    publishedDateTime,
    videoDescription,
    duration    
)
import logging

# Configure the logger
logging.basicConfig(filename='script_log.txt', level=logging.INFO)

# Log information
logging.info("Script started")



api_service_name='youtube'
api_version='v3'

youtube=googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=YT_API_KEY
)

conn = create_db_connection()
cursor = conn.cursor()

sql_query = "SELECT channel_id FROM channels"
results = cursor.execute(sql_query)
channel_ids = [row[0] for row in cursor.fetchall()]

if not channel_ids:
    raise Exception("No channel IDs found in the database. Exiting...")

for channel_id in channel_ids:
    ## get channel data (bunch of info, including playlist IDs 
    channel_data = getChannelData(channel_id) # actually uses the api
    ## find and save channel_name
    channel_name=channel_data['items'][0]['snippet']['title']
    ## parse channel data to find the "UPLOADS" playlist ID (all public videos)
    playlist_id=getPlaylistIds(channel_data) 
    ## return a list of all the video ids for the channel using upload playlistID
    video_ids=getVideoIdsFrom(playlist_id[0]) ## could save these 
    video_statistics=getVideoStatistics(video_ids) #actually uses the api
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format the timestamp
    ## note, used 151 quota units to get above info for channel with 250 videos.
    video_titles = videoTitle(video_statistics)
    video_views = viewCount(video_statistics)
    # round off the video views (are saved as float) - could do in the viewCount function
    video_views = [int(round(value)) for value in video_views]
    # parse the published date to save
    video_published_date = [video_date.strftime("%Y-%m-%d %H:%M:%S") for video_date in publishedDateTime(video_statistics)]
    video_descriptions = videoDescription(video_statistics)
    
    video_duration = duration(video_statistics)

    # Insert video_id values into the mapping table
    for i in range(len(video_ids)):
        cursor.execute("INSERT IGNORE INTO videos (video_id, channel_id, description, title, duration, published_date) VALUES (%s, %s, %s, %s, %s, %s)",
                    (video_ids[i], channel_id, video_descriptions[i],  video_titles[i], video_duration[i], video_published_date[i]))

    # Iterate through the data lists and insert data into the table with a timestamp
    for i in range(len(video_ids)):
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Format the timestamp
        cursor.execute("INSERT INTO video_views (video_id, views, timestamp) VALUES (%s, %s, %s)",
                    (video_ids[i], video_views[i], timestamp))

    # Commit the changes and close the cursor and connection
    conn.commit()
    logging.info("Logged a channel")
cursor.close()
conn.close()

print(f"Succesfully returned data for {len(channel_ids)} channel(s).")

logging.info("Script completed")
sys.exit(0)  # exits the script with an exit code of 0 (success)