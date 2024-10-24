#! /bin/env/python

from pypresence import Presence
import urllib
from urllib.request import urlopen
import json
import time
import os


apiKey = "yourapikey"
lastfmusr = "yourusername"

url_rtracks = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying="true"&user={lastfmusr}&limit=3&api_key={apiKey}&format=json'
update_interval = 30 # in seconds




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
        print("...done")

    def __del__(self):
        if self.rpc is not None and self.rpc_connected:
            self.rpc.clear()
            self.rpc.close()

    def other_is_running(self):
        pid = os.getpid()
        return (
            "python"
            in os.popen(f"ps aux | grep LastPY | grep -v {pid}").read()
        )

    #async 
    def update(self, debug=False):
        data_song = urllib.request.urlopen(url_rtracks).read().decode()
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
                length = tck_obj['track']['duration']
                if length == "0":
                    self.remaining_loops = 6
                    print("set new timeout, guessed 6 cycles")

                else:
                    self.remaining_loops = int(length) / (update_interval * 1000)
                    self.prev_url = song_url
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
        except:
            print("track could not be found, please check")
            play = "Error: could not fetch song data"
            if (song_url != self.prev_url):
                self.remaining_loops = 6
                self.prev_url = song_url
                print("set new timeout, guessed 6 cycles")         

        self.rpc.clear()
        # go to sleep
        if 0 > self.remaining_loops:
            print("song probably paused, sleeping")
            return

        if (song_album != ""):
            song_album = f" on {song_album}"
        if (song_image == ""):
            song_image = "https://media1.tenor.com/m/5iY6DCQf8r8AAAAC/patchouli-knowledge-patchy.gif"

        self.rpc.update(
            details=f"listening to {song_name}",
            state=f"by {song_artist}{song_album}",
            large_image=song_image,
            large_text= play,
            buttons=[{"label": f"{song_name} on lastfm"[0:31], "url": song_url}, {"label": f"{lastfmusr}'s profile", "url": f"https://www.last.fm/user/{lastfmusr}"}],
        )
        self.remaining_loops = self.remaining_loops - 1
        print(f"updated: {song_name}, {song_artist}, {play}, cycle {int(self.remaining_loops)}")

def main():
    client_id = "todo"
    try:
        if a := Scrobbpy(client_id):
            while(True):
                a.update(True)
                time.sleep(update_interval)
    except ConnectionRefusedError:
        print("Connection refused. Is Discord running?")


if __name__ == "__main__":
    main()