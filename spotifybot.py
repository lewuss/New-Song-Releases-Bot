from spotifykeys import *
import time
import schedule
import os
import datetime
import tweepy

keys = open("twittersongskey.txt", 'r')

CONSUMER_KEY = keys.readline().strip()
CONSUMER_SECRET = keys.readline().strip()
ACCESS_TOKEN = keys.readline().strip()
ACCESS_TOKEN_SECRET = keys.readline().strip()

TwitterAuth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
TwitterAuth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
tweeter = tweepy.API(TwitterAuth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

TOKEN = refresh('lewus')
HEADERS = {"Content-Type": "application/json",
           "Authorization": f"Bearer {TOKEN}"
           }

BASE_URL = 'https://api.spotify.com/v1/'
publiszed = {}


def update_headers(TOKEN):
    global HEADERS
    HEADERS = {"Content-Type": "application/json",
               "Authorization": f"Bearer {TOKEN}"
               }


def get_response(query, type):
    if type == "get":
        response = requests.get(query, headers=HEADERS)
    elif type == "put":
        response = requests.put(query, headers=HEADERS)
    elif type == "post":
        response = requests.post(query, headers=HEADERS)

    global TOKEN
    if response.ok:
        return response
    else:
        time.sleep(60)
        get_response(query, type)


def get_artist_id(name):
    url = f"{BASE_URL}search?q={name}&type=artist&limit=1"
    response = get_response(url, 'get')
    if not response:
        time.sleep(60)
        response = get_response(url, 'get')
    return response.json()['artists']['items'][0]['id']


def get_last_single(artist_id):
    url = f'{BASE_URL}artists/{artist_id}/albums?include_groups=single'
    response = get_response(url, 'get')
    if not response:
        time.sleep(60)
        response = get_response(url, 'get')
    return response.json()['items'][0]['name']


def get_last_album(artist_id):
    url = f'{BASE_URL}artists/{artist_id}/albums'
    response = get_response(url, 'get')
    if not response:
        time.sleep(60)
        response = get_response(url, 'get')
    return response.json()['items'][0]['name']


def get_album_info_tweet(artist_id, type):
    if type == 'single':
        url = f'{BASE_URL}artists/{artist_id}/albums?include_groups=single'
    else:
        url = f'{BASE_URL}artists/{artist_id}/albums'
    response = get_response(url, 'get')
    if not response:
        time.sleep(60)
        response = get_response(url, 'get')
    items = response.json()['items'][0]
    main_artist = items['artists'][0]['name']
    feats = []
    for artist in items['artists']:
        feats.append(artist['name'])
    del feats[0]
    feats_message = ', '.join(feats)
    poster_url = items['images'][0]['url']
    name = items['name']
    type = 'album' if items['total_tracks'] > 1 else 'single'
    link = items['external_urls']['spotify']
    if len(feats_message) > 0:
        return f'{main_artist} ft. {feats_message} - {name} has just dropped.\n \n{link}', poster_url
    else:
        return f'{main_artist} - {name} has just dropped.\n \n{link}', poster_url


def send_tweet(artist_id, type):
    message, img_url = get_album_info_tweet(artist_id, type)
    filename = 'temp.jpg'
    request = requests.get(img_url, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)
        media = tweeter.media_upload(filename)
        os.remove(filename)
    else:
        print("Unable to download image")

    if message not in publiszed:
        tweeter.update_status(status=message, media_ids=[media.media_id])
    publiszed[message] = True
    print("Tweet Sent.")

def check_if_new_single(artist_name, artist_id, old_last_track):
    new_last_track = get_last_single(artist_id)
    if new_last_track != old_last_track:
        send_tweet(artist_id, 'single')
        return new_last_track
    return old_last_track


def check_if_new_album(artist_name, artist_id, old_last_album):
    new_last_album = get_last_album(artist_id)
    if new_last_album != old_last_album:
        send_tweet(artist_id, 'album')
        return new_last_album
    return old_last_album


file = open('spotifyartist_id.txt', 'r', encoding='UTF-8')
artists_id = {}
for line in file:
    artist_name, artist_id = line.strip().split(';')
    last_single = get_last_single(artist_id)
    last_album = get_last_album(artist_id)
    artists_id[artist_name] = [artist_id, last_single, last_album]
print("Bot Launched")


def check_every_item(artists_id):
    TOKEN = refresh('lewus')
    update_headers(TOKEN)
    for key, value in artists_id.items():
        value[1] = check_if_new_single(key, value[0], value[1])
        value[2] = check_if_new_album(key, value[0], value[2])
    print(datetime.datetime.now(), time.time(), 'loop done.')


schedule.every().hour.at(":01").do(check_every_item, artists_id=artists_id)
while True:
    schedule.run_pending()
    time.sleep(1)
