#! /bin/env python

from pypresence import Presence
import urllib
import urllib.request
from urllib.request import urlopen
import json
import time
import os
import argparse

import traceback

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
parser.add_argument("-c", "--cycle", nargs="?", const=1, type=int, default=10, help="relevant if track length not found, default is 7, then multiplied by request interval")
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

class Track:
    artist = name = image = url = mbid = length = album = album_mbid = ""

class Scrobbpy:
    remaining_cycles = 0
    prev_track_url = ""
    new_track = False
    track = Track

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
        log(1, "rpc object deleted")

    def other_is_running(self):
        pid = os.getpid()
        return (
            "python"
            in os.popen(f"ps aux | grep showscrobbling.py | grep -v {pid}").read()
        )

    def req_mb(self, variant): # todo: save mbids and cycle through when no cover found
        track_mb_j = None
        if (self.track.mbid != "" and self.track.album_mbid == ""):
            log(2, "requesting musicbrainz for info")
            # https://musicbrainz.org/ws/2/recording/MBID?fmt=json&inc=aliases might help
            mb_url = f"https://musicbrainz.org/ws/2/recording/?query={variant}:{self.track.mbid}&fmt=json"
            log(3, "url: " + mb_url)
            mb_req = urllib.request.Request(mb_url, data=None, headers={'User-Agent':'ShowScrobbing/1.1 ( https://github.com/jreeee/ShowScrobbling )'})
            data_mb = urllib.request.urlopen(mb_req).read().decode()
            track_mb_j = json.loads(data_mb)
            self.track.album_mbid = track_mb_j['recordings'][0]['releases'][0]['id']
            if self.track.length == 0:
                self.track.lenth = track_mb_j['recordings'][0]['length'] # todo link up with the actual length thing
            if self.track.album == "":
                self.track.album = track_mb_j['recordings'][0]['releases'][0]['title']
            log(3, "release mbid:" + self.track.album_mbid + ", length: " + self.track.length)
        if (self.track.album_mbid != "" and track_mb_j ):
            cover_arch_url = f"https://coverartarchive.org/release/{self.track.album_mbid}"
            log(3, "coverurl: " + cover_arch_url)
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            if (cover_arch_req.getcode() == 404) and (track_mb_j != None) :
                self.track.album_mbid = track_mb_j['recordings'][0]['releases'][1]['id']
                cover_arch_url = f"https://coverartarchive.org/release/{self.track.album_mbid}"
                log(3, "2nd coverurl: " + cover_arch_url)
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            url_decoded = cover_arch_req.read().decode()
            cover_j = json.loads(url_decoded)
            self.track.image = cover_j['images'][0]['thumbnails']['large']
            log(3, "3rd img link: " + self.track.image)

        if self.track.image == "":
            self.track.image = args.image

    # anything with _j is a json object
    def update(self):
        # query lastfm for the most recent track
        data_recent_track = urllib.request.urlopen(url_recent_track).read().decode()
        recent_track_j = json.loads(data_recent_track)

        log(3, json.dumps(recent_track_j, indent=4))
        # get recent track info
        self.track.url = recent_track_j['recenttracks']['track'][0]['url']

        # in case of new track
        if (self.track.url != self.prev_track_url):
            self.prev_track_url = self.track.url
            # clear old track values
            self.track = Track
            self.new_track = True
            # split url into artist  and track name to fetch current track as standalone
            track_url_split = recent_track_j['recenttracks']['track'][0]['url'].split("/")
            url_artist = track_url_split[4]
            url_track = track_url_split[6]
            data_track_url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={lfm_api_key}&track={url_track}&artist={url_artist}&username={lfm_usr}&format=json'
            log(3, data_track_url)

            try:
                # api call to get the track
                data_track = urllib.request.urlopen(data_track_url).read().decode()
                track_j = json.loads(data_track)

                log(3, json.dumps(track_j, indent=4))

                user_playcount = track_j['track']['userplaycount']
                print_count = "times" if user_playcount != "1" else "time"

                loved_status = track_j['track']['userloved']
                print_loves = "" if loved_status != "1" else " and loves it 🤍"

                print_hover = f"{lfm_usr} listened to this track {user_playcount} {print_count}{print_loves}"

                self.track.length = track_j['track']['duration']
                if self.track.length == "0":
                    self.remaining_cycles = args.cycle
                    log(2, "set default timeout")
                else:
                    self.remaining_cycles = int(self.track.length) / (args.request * 1000) + 1
                    log(2, "set new timeout")

                self.track.image = recent_track_j['recenttracks']['track'][0]['image'][3]['#text'] # Could be none
                self.track.album = recent_track_j['recenttracks']['track'][0]['album']['#text']
                self.track.album_mbid = recent_track_j['recenttracks']['track'][0]['album']['mbid']

                log(3, "1st img link: " + self.track.image)
                if self.track.image == "":
                    log(3, "2nd img link: " + self.track.image)
                    self.track.image = track_j['track']['image'][3]['#text']

            except KeyError:
                # happens when e.g. lastfm returns a track not found
                log(1, "track info could not be found, please check your scrobbler")
                self.remaining_cycles = args.cycle
                print_hover = "Error: could not fetch song data from lastfm"
                log(2, "set default timeout")

            except Exception as e:
                log(1, str(e) + " occurred in " + traceback.format_exc())
                self.remaining_cycles = args.cycle
                log(2, "set default timeout")

        # go to sleep (return to main) if cycles are exhausted
        if 0 > self.remaining_cycles:
            self.rpc.clear()
            log(1, "song probably paused, sleeping")
            return

        # create new track rpc 
        if self.new_track:
            self.track.artist = recent_track_j['recenttracks']['track'][0]['artist']['#text']
            self.track.name = recent_track_j['recenttracks']['track'][0]['name']
            self.track.mbid = recent_track_j['recenttracks']['track'][0]['mbid']

            if (self.track.image == ""):
                query_worked = False
                try:
                    self.req_mb("tid")
                    query_worked = True
                except:
                    log(2, "musicbrainz tid query failed")
                if not query_worked:
                    try:
                        self.req_mb("rid")
                    except:
                        log(1, "musicbrainz query failed")
                        self.track.image = default_track_image

            if (self.track.album != ""):
                self.track.album = f" on {self.track.album}"
            if (print_hover == None):
                print_hover = "error fetching playcount data from lastfm"
            self.rpc.clear()
            self.rpc.update(
                details=f"listening to {self.track.name}",
                state=f"by {self.track.artist}{self.track.album}",
                large_image= self.track.image,
                large_text= print_hover,
                buttons=[{"label": f"{self.track.name} on lastfm"[0:31], "url": self.track.url}, {"label": f"{lfm_usr}'s profile", "url": f"https://www.last.fm/user/{lfm_usr}"}],
            )
            self.new_track = False
            log(1, f"playing: {self.track.name}, {self.track.artist}, {print_hover}")

        self.remaining_cycles = self.remaining_cycles - 1
        log(2, f"cycles remaining: {int(self.remaining_cycles)}")

# -----------------------------------------------------------

def main():
    try:
        if rpc := Scrobbpy(client_id):
            while(True):
                try:
                  rpc.update()
                except Exception as e:
                    log(1, str(e) + " occurred in " + traceback.format_exc())
                    log(1, f"trying again in {args.request}s")
                time.sleep(args.request)
    except ConnectionRefusedError:
        log(1, "connection refused - is discord running?")
    except KeyboardInterrupt:
        log(1, "exiting")
        del rpc
        exit(0)

if __name__ == "__main__":
    main()
