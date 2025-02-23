"""
util functions and data types
"""

import traceback
from pypresence import exceptions

from framework import constants as const


GLOBAL_LOG_LEVEL = 1


def log(loglevel, content):
    """simple logging"""
    if loglevel <= GLOBAL_LOG_LEVEL:
        print(content)


def throw_error(errtype):
    """prints error message (and traceback)"""
    match errtype:
        case exceptions.ServerError:
            print("\nSERVER ERROR: couldn't update rpc")
        case exceptions.ResponseTimeout:
            print("\nTIMEOUT ERROR: no respone in time")
        case exceptions.PipeClosed:
            print("\nPIPE ERROR: is Discord running?")
    log(3, "\n\nTraceback:\n\n" + traceback.format_exc())


def create_hover_text(track_info_j):
    """hover text for the rpc"""
    try:
        user_playcount = track_info_j["track"]["userplaycount"]
        print_count = "times" if user_playcount != "1" else "time"

        loved_status = track_info_j["track"]["userloved"]
        print_loves = "" if loved_status != "1" else " and loves it 🤍"

        return f"{const.USR} listened to this track {user_playcount} {print_count}{print_loves}"
    except KeyError:
        log(2, "lastfm track info query failed")
        return "error fetching playcount data from lastfm"


class Track:
    """basic Track object"""

    artist = name = image = url = mbid = album = album_mbid = ""
    length = 0

    def __init__(self, recent_tracks_j):
        recent_track = recent_tracks_j["recenttracks"]["track"][0]
        # the lastfm image tends to sometimes be this default gray star thing
        # self.image = recent_track["image"][3]["#text"]
        self.album = recent_track["album"]["#text"]
        self.album_mbid = recent_track["album"]["mbid"]
        self.artist = recent_track["artist"]["#text"]
        self.name = recent_track["name"]
        self.mbid = recent_track["mbid"]

    def to_cacheable_obj(self):
        """write track object into cache"""
        # quit if no mbids are present as we only search with those for consistencys sake
        if self.album_mbid == "" and self.mbid == "":
            return
        # technically we don't need the track mbid, name or album as this is contained in the
        # manadatory lfm recenttracks query
        track_j = {
            "mbid": self.mbid,
            "album_mbid": self.album_mbid,
            "title": self.name,
            "artist": self.artist,
            "length": self.length,
            "cover": self.image,
        }


class TrackInfo:
    """basic TrackInfo object that stores track related states"""

    starttime = 0
    prev_track_url = ""
    new_track = False

    def __init__(self, st, ptu, nt):
        self.starttime = st
        self.prev_track_url = ptu
        self.new_track = nt
