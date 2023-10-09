# import pandas as pd
# import numpy as np
# from re import S
from itertools import compress
from timeit import timeit
import googleapiclient.discovery
import googleapiclient.errors
# from google.oauth2 import service_account
# from google.cloud import vision
from dateutil import parser
# from proto import INT32
from datetime import timedelta, datetime, timezone
from config import YT_API_KEY

api_service_name='youtube'
api_version='v3'
key = YT_API_KEY

# def openScript():
#     """helper to reload script"""
#     return open("get_related.py").read()

# def averageList(list):
#     total=sum(list)
#     count=len(list)
#     return total/count

# def counter(listToCount):
#     """helper to count values"""
#     values=list(set(listToCount))
#     counts=[]
#     for value in values:
#         n=0
#         for item in listToCount:
#             if value==item:
#                 n+=1
#         counts.append(n)
#     return [values,counts] 




youtube=googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=key
)


def getRelatedVideos(videoId):
    """Get related video set from API"""
    request=youtube.search().list(
        part='snippet',
        type='video',
        maxResults=50,
        relatedToVideoId=videoId
    )
    response=request.execute()
    return response

def getChannelData(channelIds):
    """pass in channel id or channel ids and get some data back"""
    request=youtube.channels().list(
        part='snippet,statistics,contentDetails',
        id=channelIds
    )
    response=request.execute()
    return response

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

# def relatedChannelCount(relatedVideos):
#     """Function to return count of related channels"""
#     channelTitles = getResponseItems(relatedVideos,'snippet','channelTitle')
#     counts=counter(channelTitles)
#     [print('{:60s}'.format(x),'\t','{:,.0f}'.format(y)) for x,y in zip(counts[0],counts[1])]

def printChannelViews(channelData):
    """Silly function to print out channel, views, and avg view count"""
    channelNames=getResponseItems(channelData,'snippet','title')
    channelViews=getResponseItems(channelData,'statistics','viewCount')
    channelVideos=getResponseItems(channelData,'statistics','videoCount')
    averageViews=[eval(views)/eval(videos) for views,videos in zip(channelViews, channelVideos)]
    [print('{:<60s}'.format(x),'\t',"{:,.0f}".format(y)) for x,y in zip(channelNames,averageViews)]

def channelNameFrom(videoStatistics): 
    """Return channel Name from videoStatistics object"""
    return videoStatistics['items'][0]['snippet']['channelTitle']

def daysFromToday(datetimes,daysStart,daysEnd):
    """Silly helper function for checking date differences. Used in videoViewsByDate"""
    # for example, is this date between 30 days and 60 days = daysFromToday(date,30,60)
    today=datetime.now(timezone.utc)
    afterStart=[(today-datetime) >= timedelta(days=daysStart) for datetime in datetimes]
    beforeEnd=[(today-datetime) < timedelta(days=daysEnd) for datetime in datetimes]
    return [after and before for after,before in zip(afterStart,beforeEnd)]

# def videoViewsByDate(videoStatistics):
#     """Pop in a videoStatistics object and get summary of views by date"""
#     publishedAt=[parser.parse(item['snippet']['publishedAt']) for item in videoStatistics['items']]
#     views=[float(item['statistics']['viewCount']) for item in videoStatistics['items']]

#     # calculate bins of video views index
#     index30days=daysFromToday(publishedAt,0,30)
#     index60days=daysFromToday(publishedAt,30,60)
#     index90days=daysFromToday(publishedAt,60,90)
#     average30=averageList(list(compress(views,index30days)))
#     average60=averageList(list(compress(views,index60days)))
#     average90=averageList(list(compress(views,index90days)))
#     [print('{:,.0f}'.format(x)) for x in [average30,average60,average90]]

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
