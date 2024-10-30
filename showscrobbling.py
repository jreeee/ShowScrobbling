#! /bin/env python

from pypresence import Presence
import urllib
from urllib.request import urlopen
import json
import time
import os
import argparse

# -----------------------------------------------------------

# static values
lfm_api_key = "5125b622ac7cb502b9a857bb59a57830"
client_id = "1301054835101270117"

# the default image can be (almost) any type of image
# ideally it's roughly square and not too big, file size wise
default_track_image = "https://media.tenor.com/Hro804BGJaQAAAAj/miku-headbang.gif"

# parsing args and setting default values
parser = argparse.ArgumentParser(
    prog="ShowScrobbling",
    description="displays your scrobbles on discord"
)
parser.add_argument("-u", "--user", nargs="?", help="your lastfm username")
parser.add_argument("-l", "--loglevel", nargs="?", const=1, type=int, default=1, help="program generated output, 0: silent -> 3: debug, default 1")
parser.add_argument("-i", "--image", nargs="?", const=1, default=default_track_image, help="default image link if there's none for the track")
parser.add_argument("-c", "--cycle", nargs="?", const=1, type=int, default=7, help="relevant if track length not found, default is 7, then multiplied by request interval")
parser.add_argument("-r", "--request", nargs="?", const=1, type=int, default=30, help="interval in seconds to request lastfm api for most recent track, default 30")
args = parser.parse_args()

# set username
if args.user is not None:
    lfm_usr = args.user
else:
    lfm_usr = input("please enter your lastfm username: ")

url_recent_track = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying="true"&user={lfm_usr}&limit=1&api_key={lfm_api_key}&format=json'

# -----------------------------------------------------------

def log(level, content):
    if level <= args.loglevel:
        print(content)

# -----------------------------------------------------------

class Scrobbpy:
    remaining_cycles = 0
    prev_track_url = ""
    new_track = False

    # rpc setup
    def __init__(self, client_id):
        if self.other_is_running():
            log(1, "other instance already running.")
            exit(1)
        log(1, "init rpc")
        self
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.rpc_connected = True
        log(1, "init finished")

    # rpc cleanup
    def __del__(self):
        try:
            if self.rpc is not None and self.rpc_connected:
                self.rpc.clear()
                self.rpc.close()
        except AttributeError:
            log(2, "rpc attribute missing")
        log(1, "exiting")

    def other_is_running(self):
        pid = os.getpid()
        return (
            "python"
            in os.popen(f"ps aux | grep showscrobbling.py | grep -v {pid}").read()
        )

    # anything with _j is a json object
    def update(self):
        # query lastfm for the most recent track
        data_recent_track = urllib.request.urlopen(url_recent_track).read().decode()
        recent_track_j = json.loads(data_recent_track)
        
        log(3, recent_track_j)
        # get recent track info
        track_image = recent_track_j['recenttracks']['track'][0]['image'][3]['#text'] # Could be none
        track_artist = recent_track_j['recenttracks']['track'][0]['artist']['#text']
        track_name = recent_track_j['recenttracks']['track'][0]['name']
        track_album = recent_track_j['recenttracks']['track'][0]['album']['#text'] # Could be none
        track_url = recent_track_j['recenttracks']['track'][0]['url']

        # in case of new track
        if (track_url != self.prev_track_url):
            self.new_track = True
            self.prev_track_url = track_url
            # build url to fetch current track as standalone
            track_url_split = recent_track_j['recenttracks']['track'][0]['url'].split("/")
            url_artist = track_url_split[4]
            url_track = track_url_split[6]
            data_track_url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={lfm_api_key}&track={url_track}&artist={url_artist}&username={lfm_usr}&format=json'

            try:
                # api call to get the track
                data_track = urllib.request.urlopen(data_track_url).read().decode()
                track_j = json.loads(data_track)

                log(3, track_j)

                length = track_j['track']['duration']
                if length == "0":
                    self.remaining_cycles = args.cycle
                    log(2, "set default timeout")
                else:
                    self.remaining_cycles = int(length) / (args.request * 1000) + 1
                    log(2, "set new timeout")

                user_playcount = track_j['track']['userplaycount']
                print_count = "times" if user_playcount != 1 else "time"

                loved_status = track_j['track']['userloved']
                print_loves = "" if loved_status != "1" else " and loves it 🤍"

                print_hover = f"{lfm_usr} listened to this track {user_playcount} {print_count}{print_loves}"

            except:
                log(1, "track info could not be found, please check your scrobbler")
                print_hover = "Error: could not fetch song data"
                self.remaining_cycles = args.cycle
                log(2, "set default timeout")

        # go to sleep (return to main) if cycles are exhausted
        if 0 > self.remaining_cycles:
            self.rpc.clear()
            log(1, "song probably paused, sleeping")
            return

        # create new track rpc 
        if self.new_track:
            if (track_album != ""):
                track_album = f" on {track_album}"
            if (track_image == ""):
                track_image = args.image
            self.rpc.clear()
            self.rpc.update(
                details=f"listening to {track_name}",
                state=f"by {track_artist}{track_album}",
                large_image= track_image,
                large_text= print_hover,
                buttons=[{"label": f"{track_name} on lastfm"[0:31], "url": track_url}, {"label": f"{lfm_usr}'s profile", "url": f"https://www.last.fm/user/{lfm_usr}"}],
            )
            self.new_track = False
            log(1, f"playing: {track_name}, {track_artist}, {print_hover}")

        self.remaining_cycles = self.remaining_cycles - 1
        log(2, f"cycles remaining: {int(self.remaining_cycles)}")

# -----------------------------------------------------------

def main():
    try:
        if rpc := Scrobbpy(client_id):
            while(True):
                rpc.update()
                time.sleep(args.request)
    except ConnectionRefusedError:
        print("connection refused - is discord running?")

if __name__ == "__main__":
    main()
