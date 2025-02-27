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


def create_detail_text(track, activity_type_support) -> str:
    """detail text for the rpc"""
    # old rpc
    if not activity_type_support:
        return f"listening to {track.name}"
    # new rpc
    return track.name


def create_state_text(track) -> str:
    """state text for the rpc"""
    album = track.album
    if track.album != "":
        album = f" on {track.album}"
    return f"by {track.artist}{album}"


def create_hover_text(track_info_j, activity_type_support) -> str:
    """hover text for the rpc"""
    try:
        user_playcount = track_info_j["track"]["userplaycount"]
        loved_status = track_info_j["track"]["userloved"]
    except KeyError:
        log(2, "lastfm track info query failed")
        return "error fetching playcount data from lastfm"
    # old rpc
    print_count = "times" if user_playcount != "1" else "time"
    if not activity_type_support:
        print_loves = "" if loved_status != "1" else " and loves it 🤍"
        return f"{const.USR} listened to this track {user_playcount} {print_count}{print_loves}"
    # new rpc
    loved = "" if loved_status != "1" else " - loved track 🤍"
    return f"scrobbled {user_playcount} {print_count}{loved}"


class Track:
    """basic Track object"""

    artist = name = image = url = mbid = album = album_mbid = ""
    length = 0

    def __init__(self, recent_tracks_j, using_lfm_track_img=False):
        recent_track = recent_tracks_j["recenttracks"]["track"][0]
        # the lastfm image tends to sometimes be this default gray star thing
        if using_lfm_track_img:
            self.image = recent_track["image"][3]["#text"]
            log(3, f"1st img link: {self.image}")
        self.album = recent_track["album"]["#text"]
        self.album_mbid = recent_track["album"]["mbid"]
        self.artist = recent_track["artist"]["#text"]
        self.name = recent_track["name"]
        self.mbid = recent_track["mbid"]


class TrackInfo:
    """basic TrackInfo object that stores track related states"""

    starttime = 0
    prev_track_url = ""
    new_track = False

    def __init__(self, st, ptu, nt):
        self.starttime = st
        self.prev_track_url = ptu
        self.new_track = nt
