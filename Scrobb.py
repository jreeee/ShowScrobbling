#! /bin/env python

from pypresence import Presence
import urllib
from urllib.request import urlopen
import json
import time
import os


update_interval = 30 # in seconds

apiKey = "lastfm-api-key"
lastfmusr = "lastfm-username"
client_id = "discord-client-id" # pls discordddddd

url_rtrack = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying="true"&user={lastfmusr}&limit=1&api_key={apiKey}&format=json'





class Scrobbpy:

    def __init__(self, client_id):
        if self.other_is_running():
            print("Other instance already running.")
            exit(1)
        print("Initializing RPC...")
        self
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.rpc_connected = True
        self.remaining_loops = 0
        self.prev_url = ""
        self.new_track = False
        print("...done")

    def __del__(self):
        try:
            if self.rpc is not None and self.rpc_connected:
                self.rpc.clear()
                self.rpc.close()
        except AttributeError:
            print("rpc attribute missing")
        print("exiting")

    def other_is_running(self):
        pid = os.getpid()
        return (
            "python"
            in os.popen(f"ps aux | grep Scrobb.py | grep -v {pid}").read()
        )

    def update(self, debug=False):
        data_song = urllib.request.urlopen(url_rtrack).read().decode()
        obj_song = json.loads(data_song)
        if debug:
            print(obj_song)

        song_image = obj_song['recenttracks']['track'][0]['image'][3]['#text'] # Could be none
        song_artist = obj_song['recenttracks']['track'][0]['artist']['#text']
        song_name = obj_song['recenttracks']['track'][0]['name']
        song_album = obj_song['recenttracks']['track'][0]['album']['#text'] # Could be none
        song_url = obj_song['recenttracks']['track'][0]['url']

        split_url = obj_song['recenttracks']['track'][0]['url'].split("/")
        artist = split_url[4]
        track = split_url[6]
        
        url_track = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={apiKey}&track={track}&artist={artist}&username={lastfmusr}&format=json'
        try:
            data_track = urllib.request.urlopen(url_track).read().decode()
            tck_obj = json.loads(data_track)

            if debug:
                print(tck_obj)
            if (song_url != self.prev_url):
                self.new_track = True
                self.prev_url = song_url
                length = tck_obj['track']['duration']
                if length == "0":
                    self.remaining_loops = 7
                    print("set new timeout, guessed 7 cycles")

                else:
                    self.remaining_loops = int(length) / (update_interval * 1000) + 1
                    print("set new timeout")
        
            user_playcount = tck_obj['track']['userplaycount']
            count = "time" 
            if (user_playcount != 1):
                count = "times"
            loved_status = tck_obj['track']['userloved']
            loves = ""
            if (loved_status == "1"):
                loves = " and loves it 🤍"
            play = f"{lastfmusr} listend to this track {user_playcount} {count}{loves}"
        except: # this somehow still breaks and idk why
            print("track could not be found, please check")
            play = "Error: could not fetch song data"
            if (song_url != self.prev_url):
                self.remaining_loops = 7
                self.prev_url = song_url
                self.new_track = True
                print("set new timeout, guessed 7 cycles")

        # go to sleep
        if 0 > self.remaining_loops:
            self.rpc.clear()
            print("song probably paused, sleeping")
            return
        if self.new_track:
            if (song_album != ""):
                song_album = f" on {song_album}"
            if (song_image == ""):
                song_image = "https://media1.tenor.com/m/5iY6DCQf8r8AAAAC/patchouli-knowledge-patchy.gif"
            self.rpc.clear()
            self.rpc.update(
                details=f"listening to {song_name}",
                state=f"by {song_artist}{song_album}",
                large_image=song_image,
                large_text= play,
                buttons=[{"label": f"{song_name} on lastfm"[0:31], "url": song_url}, {"label": f"{lastfmusr}'s profile", "url": f"https://www.last.fm/user/{lastfmusr}"}],
            )
            self.new_track = False
            print(f"updated: {song_name}, {song_artist}, {play}")
        self.remaining_loops = self.remaining_loops - 1
        print(f"cycles remaining: {int(self.remaining_loops)}")

def main():
    try:
        if a := Scrobbpy(client_id):
            while(True):
                a.update()
                time.sleep(update_interval)
    except ConnectionRefusedError:
        print("Connection refused. Is Discord running?")


if __name__ == "__main__":
    main()
