"""
util functions and data types
"""

from framework import constants as const

GLOBAL_LOG_LEVEL = 1


def log(loglevel, content):
    """simple logging"""
    if loglevel <= GLOBAL_LOG_LEVEL:
        print(content)


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


def cover_from_ti_album(track_info_j):
    """try to extract the album image from the track info json"""
    try:
        url = track_info_j["track"]["album"]["image"][3]["#text"]
        log(3, "2nd img link: " + url)
        return url
    except KeyError:
        log(3, "2nd img link not found, lfm track info missing")
        return ""


class Track:
    """basic Track object"""

    artist = name = image = url = mbid = album = album_mbid = ""
    length = 0

    def __init__(self, recent_tracks_j):
        recent_track = recent_tracks_j["recenttracks"]["track"][0]
        self.image = recent_track["image"][3]["#text"]
        self.album = recent_track["album"]["#text"]
        self.album_mbid = recent_track["album"]["mbid"]
        self.artist = recent_track["artist"]["#text"]
        self.name = recent_track["name"]
        self.mbid = recent_track["mbid"]
        log(3, "1st img link: " + self.image)


class TrackInfo:
    """basic TrackInfo object that stores track related states"""

    starttime = 0
    prev_track_url = ""
    new_track = False

    def __init__(self, st, ptu, nt):
        self.starttime = st
        self.prev_track_url = ptu
        self.new_track = nt
