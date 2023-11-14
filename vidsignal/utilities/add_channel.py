from vidsignal.config import YT_API_KEY, create_db_connection
from other.utilities.get_related import getChannelData, channelPublished, channelThumbnail, channelNameFrom, searchAPI

def add_channel(channel_id, genre):
    '''Given a channel id and genre, retrieve from API and save data about channel to channel tables.
    genre should be lowercase.'''
    try:
        channel_data = getChannelData(channel_id)
        name = channelNameFrom(channel_data)
        thumbnail_uri = channelThumbnail(channel_data)
        published_date = channelPublished(channel_data)
        
        db = create_db_connection()
        cursor = db.cursor()
        # Define the SQL query to insert channel data into the 'channels' table
        sql_query = '''
            REPLACE INTO channels (channel_id, name, thumbnail_uri, published_date, genre)
            VALUES (%s, %s, %s, %s, %s)
        '''

        # Execute the query and insert the channel data
        with cursor as crsr:
            crsr.execute(sql_query, (channel_id, name, thumbnail_uri, published_date, genre))
        
        # Commit the changes to the database and close the cursor and connection
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Error processing channel_id: {channel_id} - Error: {str(e)}")
    
def lookup_channel_id(query):
    '''Search YOUTUBE api for channel_id. Note, this is expensive API query'''
    
