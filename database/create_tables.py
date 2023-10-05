import mysql.connector
from config import create_db_connection

# Create a connection to the MySQL database
connection = create_db_connection()

# Create a cursor object to execute SQL queries
cursor = connection.cursor()

create_channel_table_sql = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255)
)
"""

# Define the SQL statement to create the "videos" table
create_video_table_sql = """
CREATE TABLE IF NOT EXISTS videos (
    video_id VARCHAR(255) PRIMARY KEY,
    channel_id VARCHAR(255),
    description TEXT,
    title VARCHAR(255),
    duration DECIMAL,
    published_date DATE
)
"""

# Create video_views table if it doesn't exist
create_video_views_table = """
    CREATE TABLE IF NOT EXISTS video_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    video_id VARCHAR(255),
    views INT,
    timestamp DATETIME
)
"""
    
try:
    # Execute the SQL statement to create the table
    cursor.execute(create_channel_table_sql)
    connection.commit()
    print("Table 'channel' created successfully.")
    
    cursor.execute(create_video_table_sql)
    connection.commit()
    print("Table 'videos' created successfully.")
    
    cursor.execute(create_video_views_table)
    connection.commit()
    print("Table 'video_views' created successfully.")

except mysql.connector.Error as err:
    # Handle any errors that occur during the table creation
    print(f"Error: {err}")
finally:
    # Close the cursor and connection
    cursor.close()
    connection.close()
