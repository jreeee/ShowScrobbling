#! /bin/env python

from pypresence import Presence
import urllib
from urllib.request import urlopen
import json
import time
import os

# static values
update_interval = 30 # in seconds
log_level = 1 # 0: silent -> 3: debug

lfm_api_key = "lastfm-api-key"
lfm_usr = "lastfm-username"
client_id = "discord-client-id" # pls discordddddd


url_recent_track = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying="true"&user={lfm_usr}&limit=1&api_key={lfm_api_key}&format=json'

def log(level, content):
    if level <= log_level:
        print(content)

class Scrobbpy:
    # default values
    default_cycles = 7
    remaining_cycles = 0
    prev_track_url = ""
    new_track = False

    # rpc setup
    def __init__(self, client_id):
        if self.other_is_running():
            log(1, "Other instance already running.")
            exit(1)
        log(1, "rpc init")
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
            in os.popen(f"ps aux | grep Scrobb.py | grep -v {pid}").read()
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
                    self.remaining_cycles = self.default_cycles
                    log(2, f"set default timeout")
                else:
                    self.remaining_cycles = int(length) / (update_interval * 1000) + 1
                    log(2, "set new timeout")

                user_playcount = track_j['track']['userplaycount']
                print_count = "time" 
                if (user_playcount != 1):
                    print_count = "times"

                loved_status = track_j['track']['userloved']
                print_loves = ""
                if (loved_status == "1"):
                    print_loves = " and loves it 🤍"
                print_hover = f"{lfm_usr} listend to this track {user_playcount} {print_count}{print_loves}"

            except:
                log(1, "track info could not be found, please check your scrobbler")
                print_hover = "Error: could not fetch song data"
                if (track_url != self.prev_track_url):
                    self.remaining_cycles = self.default_cycles
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
                track_image = "https://media1.tenor.com/m/5iY6DCQf8r8AAAAC/patchouli-knowledge-patchy.gif"
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

def main():
    try:
        if rpc := Scrobbpy(client_id):
            while(True):
                rpc.update()
                time.sleep(update_interval)
    except ConnectionRefusedError:
        print("Connection refused. Is Discord running?")

if __name__ == "__main__":
    main()
