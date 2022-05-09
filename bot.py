import urllib.request
import json
from config import Config
import tweepy
import geopy as g
from datetime import date, datetime
import os


def login():
    auth = tweepy.OAuthHandler(Config.API, Config.APISECRET)
    auth.set_access_token(Config.ACESSTOKEN, Config.ACESSTOKENSECRET)
    api = tweepy.API(auth)
    return api


def getissposition():
    url = "http://api.open-notify.org/iss-now.json"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    return data


def getcountry(data):
    lat = data['iss_position']['latitude']
    lon = data['iss_position']['longitude']
    geolocator = g.Nominatim(user_agent="ISSBOT")
    loc = geolocator.reverse(f"{lat},{lon}")
    try:
        adress = loc.raw['address']
        country = adress.get('country')
    except:
        country = "Unknown"
    return country


def deg_to_dms(deg, pretty_print, ndp=4):
    deg = float(deg)
    """Convert from decimal degrees to degrees, minutes, seconds."""
    m, s = divmod(abs(deg)*3600, 60)
    d, m = divmod(m, 60)
    if deg < 0:
        d = -d
    d, m = int(d), int(m)

    if pretty_print == 'latitude':
        hemi = 'N' if d >= 0 else 'S'
    elif pretty_print == 'longitude':
        hemi = 'E' if d >= 0 else 'W'
    else:
        hemi = '?'
    return "{d:d}%C2%B0{m:d}%27{s:.{ndp:d}f}%22{hemi:1s}".format(
        d=abs(d), m=m, s=s, hemi=hemi, ndp=ndp)


def tweet(api, data, country):
    lat = data['iss_position']['latitude']
    lon = data['iss_position']['longitude']
    lats = deg_to_dms(lat, 'latitude')
    lons = deg_to_dms(lon, 'longitude')
    dt_object = datetime.fromtimestamp(data['timestamp'])
    if country != "Unknown":
        tweet = f"The ISS is currently above {country} ({dt_object.strftime('%Y-%m-%d %H:%M:%S')} Current position is {lat}, {lon}) https://www.google.com/maps/place/{lats}+{lons}"
        logger(tweet)
        api.update_status(tweet)
        logger("Tweeted"+"\n")
    else:
        tweet = f"The ISS is currently not above any country ({dt_object.strftime('%Y-%m-%d %H:%M:%S')} Current position is {lat}, {lon}) https://www.google.com/maps/place/{lats}+{lons}"
        logger(tweet)
        api.update_status(tweet)
        logger("Tweeted"+"\n")


def logger(body):
    with open(__file__[:-6]+'iss.log', 'a', encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        str = f"{timestamp} {body}\n"
        f.write(str)
        f.close()


def getlasttweet(api):
    username = "iss_track"
    tweetlist = api.user_timeline(username=username, count=1)
    tweet = tweetlist[0]
    return tweet.created_at.hour


def logcountry(country):
    with open(__file__[:-6]+'country.log', 'r', encoding="utf-8") as f:
        lines = f.readlines()
        if len(lines) > 0:
            first = True
        else:
            first = False
        f.close()
    with open(__file__[:-6]+'country.log', 'a', encoding="utf-8") as f:
        if first:
            f.write("\n"+country)
            f.close()
        else:
            f.write(country)
            f.close()


def getlastcountry():
    try:
        with open(__file__[:-6]+'country.log', 'r', encoding="utf-8") as f:
            lines = f.readlines()
            if len(lines) >= 1:
                return lines[-1]
            else:
                logcountry("Unknown")
                return "Unknown"

    except:
        with open(__file__[:-6]+'country.log', 'w', encoding="utf-8") as f:
            f.close()
        logcountry("Unknown")
        return "Unknown"


def __main__():
    api = login()
    logger("Logged in")
    print('Logged in')
    logger("Getting ISS position")
    data = getissposition()
    logger("Got ISS position")
    logger("Getting country")
    country = getcountry(data)
    logger("Got country")
    lastcountry = getlastcountry()
    print(f"Last country: {lastcountry} Current country: {country}")
    if lastcountry != country:
        logger("Country changed")
        logcountry(country)
        logger("Tweeting")
        tweet(api, data, country)
    else:
        logger("Country not changed"+"\n")
    exit(0)


if __name__ == "__main__":
    __main__()
