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

# external libraries
import urllib.request
from pypresence import Presence
from pypresence import exceptions

# local project files
from framework import args as parser
from framework import constants as const
from framework import utils
from framework import requests

# -----------------------------------------------------------

VERSION = "1.5"

# get and parse args
args = parser.parse_args()

# setting vars
if args.user is not None:
    LFM_USR = args.user
else:
    LFM_USR = const.USR
if args.loglevel != 1:
    utils.GLOBAL_LOG_LEVEL = args.loglevel

# -----------------------------------------------------------


class Scrobbpy:
    """script object"""

    prev_track_url = ""
    new_track = False
    sleeping = False
    track = utils.Track
    starttime = 0
    hovertext = None

    # rpc setup
    def __init__(self, client_id):
        if self.other_is_running():
            utils.log(1, "other instance already running.")
            sys.exit(1)
        utils.log(1, "init rpc")
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.rpc_connected = True
        utils.log(1, f"init finished, running version {VERSION}")

    # rpc cleanup
    def __del__(self):
        try:
            if self.rpc is not None and self.rpc_connected:
                self.rpc.clear()
                self.rpc.close()
        except AttributeError:
            utils.log(2, "rpc attribute missing")
        utils.log(1, "rpc object deleted")

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
            utils.log(1, "no song playing, sleeping")

    def req_mb(self, variant):  # todo: save mbids and cycle through when no cover found
        """send a request to MusicBrainz to get the mbid of the track and get coverart"""
        track_mb_j = None
        if self.track.mbid != "" and self.track.album_mbid == "":
            utils.log(2, "requesting musicbrainz for info")
            # https://musicbrainz.org/ws/2/recording/MBID?fmt=json&inc=aliases might help
            track_mb_j = requests.get_mb_json(variant, self.track.mbid, VERSION)
            if track_mb_j is None:
                return
            self.track.album_mbid = track_mb_j["recordings"][0]["releases"][0]["id"]
            if self.track.length == 0:
                # todo link up with the actual length thing
                self.track.lenth = track_mb_j["recordings"][0]["length"]
            if self.track.album == "":
                self.track.album = track_mb_j["recordings"][0]["releases"][0]["title"]
            utils.log(
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
            utils.log(3, "coverurl: " + cover_arch_url)
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            # todo loop over
            if (cover_arch_req.getcode() == 404) and (track_mb_j is not None):
                self.track.album_mbid = track_mb_j["recordings"][0]["releases"][1]["id"]
                cover_arch_url = (
                    f"https://coverartarchive.org/release/{self.track.album_mbid}"
                )
                utils.log(3, "2nd coverurl: " + cover_arch_url)
            cover_j = requests.get_json(cover_arch_url)
            self.track.image = cover_j["images"][0]["thumbnails"]["large"]
            utils.log(3, "3rd img link: " + self.track.image)

        if self.track.image == "":
            self.track.image = args.image

    # anything with _j is a json object
    def update(self):
        """called every interval to check the current status"""

        # query lastfm for the most recent track
        recent_track_j = requests.get_json(const.URL_RECENT_TRACK)

        # get recent track info
        playing = recent_track_j["recenttracks"]["track"][0].get("@attr", {})
        if len(playing) == 0:
            self.sleep()
            return
        # i don't think this is necessary, but better safe than sorry
        key, value = next(iter(playing.items()))
        if not (key == "nowplaying" and value == "true"):
            self.sleep()
            return

        self.track.url = recent_track_j["recenttracks"]["track"][0]["url"]

        # in case of new track
        if self.track.url != self.prev_track_url:
            # roughly the start time, +- args.request / 2 (15s)
            self.starttime = time.time() - (args.request / 2)
            self.new_track = True
            self.sleeping = False
            self.prev_track_url = self.track.url
            # clear old track values
            self.track = utils.Track.__new__(utils.Track)
            # split url into artist  and track name to fetch current track as standalone
            data_track_url = requests.track_info_url(recent_track_j)

            # Try track image, could be empty
            self.track.image = recent_track_j["recenttracks"]["track"][0]["image"][3][
                "#text"
            ]
            utils.log(3, "1st img link: " + self.track.image)
            self.track.album = recent_track_j["recenttracks"]["track"][0]["album"][
                "#text"
            ]
            self.track.album_mbid = recent_track_j["recenttracks"]["track"][0]["album"][
                "mbid"
            ]

            try:
                # api call to get track for more info since this can result in a
                # "track not found", everything here is in a try block
                track_j = requests.get_json(data_track_url)

                # hover text for the rpc
                user_playcount = track_j["track"]["userplaycount"]
                print_count = "times" if user_playcount != "1" else "time"

                loved_status = track_j["track"]["userloved"]
                print_loves = "" if loved_status != "1" else " and loves it 🤍"

                self.hovertext = f"{LFM_USR} listened to this track {user_playcount} {print_count}{print_loves}"

                # if we get no track image, test if there's a album and get its image instead
                if self.track.image == "" and track_j["track"].get("album", {}) != {}:
                    utils.log(3, "2nd img link: " + self.track.image)
                    self.track.image = track_j["track"]["album"]["image"][3]["#text"]

            except KeyError:
                # happens when e.g. lastfm returns a track not found
                utils.log(
                    1, "track info could not be found, please check your scrobbler"
                )
                self.hovertext = None

            except Exception as e:
                utils.log(1, str(e) + " occurred in " + traceback.format_exc())
                self.hovertext = None

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
                    utils.log(2, "musicbrainz tid query failed")
                if not query_worked:
                    try:
                        self.req_mb("rid")
                    except:
                        utils.log(1, "musicbrainz query failed")
                        self.track.image = const.DEFAULT_TRACK_IMAGE

            if self.track.album != "":
                self.track.album = f" on {self.track.album}"
            if self.hovertext is None:
                self.hovertext = "error fetching playcount data from lastfm"
            self.rpc.clear()
            try:
                self.rpc.update(
                    details=f"listening to {self.track.name}",
                    start=self.starttime,
                    state=f"by {self.track.artist}{self.track.album}",
                    large_image=self.track.image,
                    large_text=self.hovertext,
                    buttons=[
                        {
                            "label": "song on last.fm",
                            "url": self.prev_track_url,
                        },
                        {
                            "label": f"{LFM_USR}'s profile"[0:31],
                            "url": f"https://www.last.fm/user/{LFM_USR}",
                        },
                    ],
                )
                self.new_track = False
                utils.log(
                    1,
                    f"playing: {self.track.name}, {self.track.artist}, {self.hovertext}",
                )
            except exceptions.ServerError:
                utils.log(
                    1,
                    "SERVER ERROR: couldn't update rpc \n\nTraceback:\n\n"
                    + traceback.format_exc(),
                )
            except exceptions.ResponseTimeout:
                utils.log(
                    1,
                    "ERROR: RESPONSE TIMEOUT - no answer from server \n\nTraceback:\n\n"
                    + traceback.format_exc(),
                )
            except exceptions.PipeClosed:
                utils.log(
                    1,
                    "ERROR: PIPE CLOSED: is discord running? \n\nTraceback:\n\n"
                    + traceback.format_exc(),
                )


# -----------------------------------------------------------


def main():
    """main method for ShowScrobbling"""
    try:
        if rpc := Scrobbpy(const.CLIENT_ID):
            while True:
                try:
                    rpc.update()
                except Exception as e:
                    utils.log(1, str(e) + " occurred in " + traceback.format_exc())
                    utils.log(1, f"trying again in {args.request}s")
                time.sleep(args.request)
    except ConnectionRefusedError:
        utils.log(1, "connection refused - is discord running?")
    except KeyboardInterrupt:
        utils.log(1, "exiting")
        del rpc
        sys.exit(0)


if __name__ == "__main__":
    main()
