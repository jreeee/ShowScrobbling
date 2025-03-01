"""
functions related to API queries
"""

import urllib.request
from urllib.error import HTTPError
import json

from framework import utils
from framework import constants as const


def get_json(url):
    """return json object for given url"""
    try:
        url_obj = urllib.request.urlopen(url)
        if url_obj.getcode() == 404:
            utils.log(2, "no site")
            return None
        url_decoded = url_obj.read().decode()
        json_obj = json.loads(url_decoded)
        utils.log(3, json.dumps(json_obj, indent=2))
        return json_obj
    except HTTPError:
        return ""


def get_mb_json(variant, mbid, version):
    """get json object from musicbrainz using tid or rid query"""
    mb_url = f"{const.MB_REC_QRY}{variant}:{mbid}&fmt=json"
    utils.log(3, "url: " + mb_url)
    mb_req = urllib.request.Request(
        mb_url,
        data=None,
        headers={
            "User-Agent": f"ShowScrobbing/{version} ( https://github.com/jreeee/ShowScrobbling )"
        },
    )
    return get_json(mb_req)


def track_info_url(track_json):
    """create the lastfm track info url using the recent track"""
    track_url_split = track_json["recenttracks"]["track"][0]["url"].split("/")
    url_artist = track_url_split[4]
    url_track = track_url_split[6]
    info_url = (
        f"{const.URL_TRACK_INFO}&track={url_track}&artist={url_artist}&format=json"
    )
    utils.log(3, info_url)
    return info_url


def req_mb(track, variant, ver) -> utils.Track:
    """send a request to MusicBrainz to get the mbid of the track and get coverart"""
    track_mb_j = None
    # track has mbid, album does not
    if track.mbid != "" and track.album_mbid == "":
        utils.log(2, "requesting musicbrainz for info")
        # https://musicbrainz.org/ws/2/recording/MBID?fmt=json&inc=aliases might help
        track_mb_j = get_mb_json(variant, track.mbid, ver)
        if track_mb_j is None:
            return track
        track.album_mbid = track_mb_j["recordings"][0]["releases"][0]["id"]
        if track.length == 0:
            track.lenth = int(track_mb_j["recordings"][0]["length"])
        if track.album == "":
            track.album = track_mb_j["recordings"][0]["releases"][0]["title"]
        utils.log(
            3,
            "release mbid:" + str(track.album_mbid) + ", length: " + str(track.length),
        )
    # album has mbid
    if track.album_mbid != "" and track.image == "":
        cover_arch_url = f"https://coverartarchive.org/release/{track.album_mbid}"
        utils.log(3, "coverurl: " + cover_arch_url)
        try:
            cover_arch_req = urllib.request.urlopen(cover_arch_url)
            # TODO loop over & look into releases for coverart

            if (cover_arch_req.getcode() == 404) and (track_mb_j is not None):
                track.album_mbid = track_mb_j["recordings"][0]["releases"][1]["id"]
                cover_arch_url = (
                    f"https://coverartarchive.org/release/{track.album_mbid}"
                )
                utils.log(3, "2nd coverurl: " + cover_arch_url)
            cover_j = get_json(cover_arch_url)
            track.image = cover_j["images"][0]["thumbnails"]["large"]
            utils.log(3, "3rd img link: " + track.image)
        except (KeyError, HTTPError):
            utils.log(3, "key/http error, moving on")
            track.image = ""
    return track


def get_cover_image(track: utils.Track, track_info_j, ver) -> utils.Track:
    """querying for a image link"""

    # lastfm album cover based on track_info
    try:
        track.length = track_info_j["track"]["duration"]
        if track.image == "":
            track.image = track_info_j["track"]["album"]["image"][3]["#text"]
        if track.image != "":
            track.img_link_nr = 2
            utils.log(3, "2nd img link: " + track.image)
            return track
    except KeyError:
        utils.log(3, "2nd img link not found, lfm track info missing")

    # musicbrainz album artwork based on track_info
    try:
        updatedtrack = req_mb(track, "tid", ver)
        updatedtrack.img_link_nr = 3
    except IndexError:
        utils.log(3, "musicbrainz tid query failed")
        try:
            updatedtrack = req_mb(track, "rid", ver)
            updatedtrack.img_link_nr = 4
        except IndexError:
            utils.log(3, "musicbrainz rid query failed")
            utils.log(2, "musicbrainz query failed")

    if updatedtrack is not None:
        track = updatedtrack
    # edge cases that would prevent pypresence from updating
    if track.image == "" or len(track.image) >= 256:
        track.image = "fallback"
        track.img_link_nr = -1
    return track
