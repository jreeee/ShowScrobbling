#! /usr/bin/env python

"""
ShowScrobbling
a small-ish python script that uses Pypresence and last.fm (and MusicBrainz)
to display coverart of your currently scrobbling song in Discord 
"""

# system libraries
import sys
import os
import time
import traceback
import json

# external libraries
import urllib.request
from pypresence import Presence

# local project files
import framework.args as parser
import framework.constants as const

# -----------------------------------------------------------

VERSION = "1.4"

# get and parse args
args = parser.parse_args()

# set username
if args.user is not None:
    LFM_USR = args.user
else:
    LFM_USR = const.USR

# -----------------------------------------------------------


def log(level, content):
    """basic logging including priorities"""
    if level <= args.loglevel:
        print(content)


# -----------------------------------------------------------


class Track:
    """basic Track object"""

    artist = name = image = url = mbid = length = album = album_mbid = ""


class Scrobbpy:
    """script object"""

    prev_track_url = ""
    new_track = False
    sleeping = False
    track = Track
    starttime = 0

    # rpc setup
    def __init__(self, client_id):
        if self.other_is_running():
            log(1, "other instance already running.")
            sys.exit(1)
        log(1, "init rpc")
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.rpc_connected = True
        log(1, f"init finished, running version {VERSION}")

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
        """check if another instance is already running"""
        pid = os.getpid()
        return (
            "python"
            in os.popen(f"ps aux | grep showscrobbling.py | grep -v {pid}").read()
        )

    def sleep(self):
        """zzzzzzzzz"""
        # all of the following things need to be set just once for a given sleep period
        if not self.sleeping:
            self.rpc.clear()
            self.sleeping = True
            self.prev_track_url = ""
            log(1, "no song playing, sleeping")

    def req_mb(self, variant):  # todo: save mbids and cycle through when no cover found
        """send a request to MusicBrainz to get the mbid of the track and get coverart"""
        track_mb_j = None
        if self.track.mbid != "" and self.track.album_mbid == "":
            log(2, "requesting musicbrainz for info")
            # https://musicbrainz.org/ws/2/recording/MBID?fmt=json&inc=aliases might help
            mb_url = f"{const.MB_REC_QRY}{variant}:{self.track.mbid}&fmt=json"
            log(3, "url: " + mb_url)
            mb_req = urllib.request.Request(
                mb_url,
                data=None,
                headers={
                    "User-Agent": f"ShowScrobbing/{VERSION} ( https://github.com/jreeee/ShowScrobbling )"
                },
            )
            data_mb = urllib.request.urlopen(mb_req).read().decode()
            track_mb_j = json.loads(data_mb)
            self.track.album_mbid = track_mb_j["recordings"][0]["releases"][0]["id"]
            if self.track.length == 0:
                # todo link up with the actual length thing
                self.track.lenth = track_mb_j["recordings"][0]["length"]
            if self.track.album == "":
                self.track.album = track_mb_j["recordings"][0]["releases"][0]["title"]
            log(
                3,
                "release mbid:"
                + self.track.album_mbid
                + ", length: "
                + self.track.length,
            )
        if self.track.album_mbid != "" and track_mb_j:
            cover_arch_url = (
                f"https://coverartarchive.org/release/{self.track.album_mbid}"
            )
            log(3, "coverurl: " + cover_arch_url)
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            if (cover_arch_req.getcode() == 404) and (track_mb_j is not None):
                self.track.album_mbid = track_mb_j["recordings"][0]["releases"][1]["id"]
                cover_arch_url = (
                    f"https://coverartarchive.org/release/{self.track.album_mbid}"
                )
                log(3, "2nd coverurl: " + cover_arch_url)
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            url_decoded = cover_arch_req.read().decode()
            cover_j = json.loads(url_decoded)
            self.track.image = cover_j["images"][0]["thumbnails"]["large"]
            log(3, "3rd img link: " + self.track.image)

        if self.track.image == "":
            self.track.image = args.image

    # anything with _j is a json object
    def update(self):
        """called every interval to check the current status"""

        # query lastfm for the most recent track
        data_recent_track = (
            urllib.request.urlopen(const.URL_RECENT_TRACK).read().decode()
        )
        recent_track_j = json.loads(data_recent_track)

        log(3, json.dumps(recent_track_j, indent=4))
        # get recent track info
        playing = recent_track_j["recenttracks"]["track"][0].get("@attr", {})
        if len(playing) == 0:
            self.sleep()
            return
        # i don't think this is necessary, but better safe than sorry
        key, value = next(iter(playing.items()))
        if key != "nowplaying" or value != "true":
            self.sleep()
            return

        self.track.url = recent_track_j["recenttracks"]["track"][0]["url"]

        # in case of new track
        if self.track.url != self.prev_track_url:
            # roughly the start time, +- args.request / 2 (15s)
            starttime = time.time() - (args.request / 2)
            self.new_track = True
            self.sleeping = False
            self.prev_track_url = self.track.url
            # clear old track values
            self.track = Track.__new__(Track)
            # split url into artist  and track name to fetch current track as standalone
            track_url_split = recent_track_j["recenttracks"]["track"][0]["url"].split(
                "/"
            )
            url_artist = track_url_split[4]
            url_track = track_url_split[6]
            data_track_url = f"{const.URL_TRACK_INFO}&track={url_track}&artist={url_artist}&format=json"
            log(3, data_track_url)

            # Try track image, could be empty
            self.track.image = recent_track_j["recenttracks"]["track"][0]["image"][3][
                "#text"
            ]
            log(3, "1st img link: " + self.track.image)
            self.track.album = recent_track_j["recenttracks"]["track"][0]["album"][
                "#text"
            ]
            self.track.album_mbid = recent_track_j["recenttracks"]["track"][0]["album"][
                "mbid"
            ]

            try:
                # api call to get track for more info since this can result in a
                # "track not found", everything here is in a try block
                data_track = urllib.request.urlopen(data_track_url).read().decode()
                track_j = json.loads(data_track)

                log(3, json.dumps(track_j, indent=4))

                # hover text for the rpc
                user_playcount = track_j["track"]["userplaycount"]
                print_count = "times" if user_playcount != "1" else "time"

                loved_status = track_j["track"]["userloved"]
                print_loves = "" if loved_status != "1" else " and loves it 🤍"

                print_hover = f"{LFM_USR} listened to this track {user_playcount} {print_count}{print_loves}"

                # if we get no track image, try the album image instead
                if self.track.image == "":
                    log(3, "2nd img link: " + self.track.image)
                    self.track.image = track_j["track"]["album"]["image"][3]["#text"]

            except KeyError:
                # happens when e.g. lastfm returns a track not found
                log(1, "track info could not be found, please check your scrobbler")
                print_hover = "Error: could not fetch song data from lastfm"

            except Exception as e:
                log(1, str(e) + " occurred in " + traceback.format_exc())

        # create new track rpc
        if self.new_track:
            self.track.artist = recent_track_j["recenttracks"]["track"][0]["artist"][
                "#text"
            ]
            self.track.name = recent_track_j["recenttracks"]["track"][0]["name"]
            self.track.mbid = recent_track_j["recenttracks"]["track"][0]["mbid"]

            if self.track.image == "":
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
                        self.track.image = const.DEFAULT_TRACK_IMAGE

            if self.track.album != "":
                self.track.album = f" on {self.track.album}"
            if print_hover is None:
                print_hover = "error fetching playcount data from lastfm"
            self.rpc.clear()
            self.rpc.update(
                details=f"listening to {self.track.name}",
                start=starttime,
                state=f"by {self.track.artist}{self.track.album}",
                large_image=self.track.image,
                large_text=print_hover,
                buttons=[
                    {
                        "label": f"{self.track.name} on lastfm"[0:31],
                        "url": self.track.url,
                    },
                    {
                        "label": f"{LFM_USR}'s profile",
                        "url": f"https://www.last.fm/user/{LFM_USR}",
                    },
                ],
            )
            self.new_track = False
            log(1, f"playing: {self.track.name}, {self.track.artist}, {print_hover}")

# -----------------------------------------------------------


def main():
    """main method for ShowScrobbling"""
    try:
        if rpc := Scrobbpy(const.CLIENT_ID):
            while True:
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
        sys.exit(0)


if __name__ == "__main__":
    main()
