import googleapiclient.discovery
import googleapiclient.errors
from dateutil import parser
from datetime import timedelta, datetime
from . config import YT_API_KEY

api_service_name='youtube'
api_version='v3'
key = YT_API_KEY

youtube=googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=key
)

def getChannelData(channelIds):
    """pass in channel id or channel ids and get some data back"""
    request=youtube.channels().list(
        part='snippet,statistics,contentDetails,topicDetails',
        id=channelIds
    )
    response=request.execute()
    return response

def channelPublished(channelData):
    """Get the channel published date from the API"""
    return channelData['items'][0]['snippet']['publishedAt']

def channelThumbnail(channelData):
    """Return thumbnail URI from channel data"""
    return channelData['items'][0]['snippet']['thumbnails']['default']['url']

def getVideoIdsFrom(playlistId):
    """Pass in youtube playlist Id and get the video IDs back."""
    ## first we need to query playlistItems to get id of each video
    ## this only takes one playlist at a time
    request=youtube.playlistItems().list(
        playlistId=playlistId,
        maxResults=50,
        part='snippet'
    )
    response=request.execute()

    while 'nextPageToken' in response.keys(): # check if the nextPageToken is there
        request=youtube.playlistItems().list(
           playlistId=playlistId,
           maxResults=50,
           part='snippet',
           pageToken=response['nextPageToken']
        )
        nextResponse=request.execute()
        response['items'].extend(nextResponse['items'])
        if 'nextPageToken' in nextResponse.keys(): # if we still have more pages, swap tokens
            response['nextPageToken']=nextResponse['nextPageToken']
        else:
            break
    return [item['snippet']['resourceId']['videoId'] for item in response['items']] # return list of video ids

def getVideoStatistics(videoIds):
    """Pass in video IDs and get statistics about video
    This thing gets tons of data: views, duration, upload date
    thumbnail uri, description, and more
    """
    ### need to break this up into calls of 50 videos at a time
    ## get video length, figure out how many times have to call
    ## keep track of number of times called
    ## aggregate all the differrent results
    videoIdCount=len(videoIds)
    timesToRun=videoIdCount//50+(videoIdCount%50>0)
    timesRan=0 
    while timesRan<timesToRun:
        searchIndex=50+timesRan*50
        videoIdsToSearch=videoIds[timesRan*50:searchIndex]
        request=youtube.videos().list(
        id=videoIdsToSearch,
        part='snippet,statistics,contentDetails'
        )
        if timesRan==0:
            response=request.execute()
        else:
            nextResponse=request.execute()
            response['items'].extend(nextResponse['items'])
        timesRan+=1
    return response
    
def viewException(item):
    """helper for weird no viewcount error"""
    try:
        return item['statistics']['viewCount']
    except:
        return 0

def getResponseItems(response,part,thing):
    """pass in json response and pull out pieces"""
    return [item[part][thing] for item in response['items']]

def getResponseKeys(response, part):
    """parse response for keys given a part"""
    items=response['items'][0][part].keys()
    print(*items, sep='\n')

def getRelatedVideoIds(relatedVideos):
    """helper to get ids or related videos"""
    return [item['id']['videoId'] for item in relatedVideos['items']]

def generateThumbnailURLs(videoIds):
    """Helper function to make videoId into yt thumbnail url"""
    base='https://i.ytimg.com/vi/'
    end='/maxresdefault.jpg'
    return [base+videoId+end for videoId in videoIds]

def getPlaylistIds(channelData):
    """get the uploads playlist id for the videos"""
    relatedPlaylists=getResponseItems(channelData,'contentDetails','relatedPlaylists')
    uploadsId=[playlistId['uploads'] for playlistId in relatedPlaylists]
    return uploadsId

def channelNameFrom(videoStatistics): 
    """Return channel Name from videoStatistics object"""
    return videoStatistics['items'][0]['snippet']['channelTitle']

def viewCount(videoStatistics):
    """Get list of viewCount as numeric from videoStatistics"""
    viewCount=[]
    [viewCount.append(float(views['statistics']['viewCount'])) for views in videoStatistics['items']]
    return viewCount

def durationException(item):
    """helper for 0D time stamp"""
    try: 
        return parser.parse(item['contentDetails']['duration'].strip('PT'))
    except:
        return datetime.min

def duration(videoStatistics):
    """Get list of video durations in minutes from videoStatistics"""
    zero = timedelta(0)
    duration=[]
    [duration.append(durationException(time)) for time in videoStatistics['items']]
    return [round(time.hour*60 + time.minute + time.second/60,1) for time in duration]

def publishedAt(videoStatistics):
    """Get list of video publish dates as datetime"""
    publishedAt=[parser.isoparse(publishedAt['snippet']['publishedAt']).date() for publishedAt in videoStatistics['items']]
    return publishedAt

def publishedTime(videoStatistics):
    """get list of video published time"""
    publishedTime=[parser.isoparse(publishedAt['snippet']['publishedAt']).time() for publishedAt in videoStatistics['items']]
    return publishedTime

def publishedDateTime(videoStatistics):
    """Get a list of video published date and time"""
    # Parse 'publishedAt' and convert it to datetime objects
    publishedDateTime = [
        parser.isoparse(publishedAt['snippet']['publishedAt']) for publishedAt in videoStatistics['items']
    ]
    return publishedDateTime

def videoTitle(videoStatistics):
    """Get list of video titles from videoStatistics"""
    return [videoTitle['snippet']['title'] for videoTitle in videoStatistics['items']]

def videoIdsFrom(videoStatistics):
    """Return a list of videoId from videoStatistics"""
    return [item['id'] for item in videoStatistics['items']]

def videoDescription(videoStatistics):
    """get video description from video stats results"""
    return [item['snippet']['description'] for item in videoStatistics['items']]
