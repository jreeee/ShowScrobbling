"""
functions related to API queries
"""

import urllib.request
from urllib.error import HTTPError
import json

from framework import utils
from framework import constants as const

MB_API = "https://musicbrainz.org/ws/2/"


def get_json(url):
    """return json object for given url"""
    try:
        url_obj = urllib.request.urlopen(url)
        url_decoded = url_obj.read().decode()
        json_obj = json.loads(url_decoded)
        utils.log(4, json.dumps(json_obj, indent=2))
        return json_obj
    except HTTPError:
        utils.log(2, "no site")
        return ""


def get_html_cover(url) -> str:
    """return cover url from vgmdb"""
    try:
        url_obj = urllib.request.urlopen(url)
        url_decoded = url_obj.read()
        vgmdb_html = str(url_decoded)
        idx = vgmdb_html.index('property="og:image"')
        cover_idx_start = vgmdb_html.index("https:", idx)
        cover_idx_end = vgmdb_html.index('"', cover_idx_start)

        cover = vgmdb_html[cover_idx_start:cover_idx_end]
        # cover = cover_line.split('"')[0]
        utils.log(2, "vgmdb url: " + cover)
        return cover
    except (HTTPError, IndexError):
        utils.log(2, "error in vgmdb query")
        return ""


def get_mb_json(variant, mbid, version):
    """get json object from musicbrainz using tid, rid or reid query"""

    if variant != "reid":
        query = "recording/?query="
    else:
        query = "release-group/?query="

    mb_url = f"{MB_API}{query}{variant}:{mbid}&fmt=json"
    utils.log(3, "url: " + mb_url)
    mb_req = urllib.request.Request(
        mb_url,
        data=None,
        headers={
            "User-Agent": f"ShowScrobbing/{version} ( https://github.com/jreeee/ShowScrobbling )"
        },
    )
    return get_json(mb_req)


def get_vgmdb_json(form, mbid, version):
    """check mb if vgmdb is a relation"""

    res = ""
    # form is either release or release group
    mb_url = f"{MB_API}{form}/{mbid}?inc=url-rels&fmt=json"
    utils.log(3, "url: " + mb_url)
    mb_req = urllib.request.Request(
        mb_url,
        data=None,
        headers={
            "User-Agent": f"ShowScrobbing/{version} ( https://github.com/jreeee/ShowScrobbling )"
        },
    )
    query = get_json(mb_req)
    if query == "":
        return res
    for i in query["relations"]:
        if i["type"] == "vgmdb":
            res = i["url"]["resource"]
            break
    if res == "":
        return res
    utils.log(3, "url: " + res)
    vgmdb_req = urllib.request.Request(
        res,
        data=None,
        headers={
            "User-Agent": f"ShowScrobbing/{version} ( https://github.com/jreeee/ShowScrobbling )"
        },
    )
    return get_html_cover(vgmdb_req)


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


def req_mb_track(track, variant, ver) -> utils.Track:
    """send a request to MusicBrainz to get the mbid of the track and get coverart"""
    track_mb_j = None
    rel_num = 0
    # track has mbid, album does not
    if track.mbid != "" and track.album_mbid == "":
        utils.log(2, "requesting musicbrainz for info")
        track_mb_j = get_mb_json(variant, track.mbid, ver)
        if track_mb_j == "":
            return track
        # check for release with matching name
        if track.album != "":
            for i in track_mb_j["recordings"][0]["releases"]:
                if i["title"] == track.album:
                    track.album_mbid = i["id"]
                    break
                rel_num += 1
        # set values of the first release found if no album name nor album mbid
        else:
            track.album = track_mb_j["recordings"][0]["releases"][0]["title"]
            track.album_mbid = track_mb_j["recordings"][0]["releases"][0]["id"]
            rel_num = 0
        if track.length == 0:
            track.lenth = int(track_mb_j["recordings"][rel_num]["length"])

        utils.log(
            3,
            "release mbid:" + str(track.album_mbid) + ", length: " + str(track.length),
        )

        if track.image == "" and track.album_mbid != "":
            track.image = get_vgmdb_json("release", track.album_mbid, ver)

    return track

    # album has mbid


def req_album_cover(album_mbid, cover, ver):
    if album_mbid != "" and cover in ("", "fallback"):

        cover_id = ""
        image = ""
        cover_arch_url = f"https://coverartarchive.org/release/{album_mbid}"
        utils.log(3, "coverurl: " + cover_arch_url)
        try:
            urllib.request.urlopen(cover_arch_url)
            cover_j = get_json(cover_arch_url)
            if cover_j != "":
                return cover_j["images"][0]["thumbnails"]["large"]
        except HTTPError:
            utils.log(2, "no default release img, using release groups")
        track_list = get_mb_json("reid", album_mbid, ver)
        if track_list != "":
            cover_id = track_list["release-groups"][0]["id"]
            cover_j = get_json(f"https://coverartarchive.org/release-group/{cover_id}")
            if cover_j != "":
                return cover_j["images"][0]["thumbnails"]["large"]
            utils.log(3, "2nd coverurl: " + image)
        else:
            utils.log(3, "error getting link, moving on")
            return get_vgmdb_json("release", cover_id, ver)
    return cover


def get_cover_image(track: utils.Track, track_info_j, ver) -> utils.Track:
    """querying for a image link"""

    # lastfm album cover based on track_info
    try:
        track.length = track_info_j["track"]["duration"]
        track.image = track_info_j["track"]["album"]["image"][3]["#text"]
        if track.image != "":
            track.img_link_nr = 2
            utils.log(3, "2nd img link: " + track.image)
            return track
    except KeyError:
        utils.log(3, "2nd img link not found, lfm track info missing")

    # musicbrainz album artwork based on track_info
    updatedtrack = None
    try:
        updatedtrack = req_mb_track(track, "tid", ver)
        updatedtrack.image = req_album_cover(
            updatedtrack.album_mbid, updatedtrack.image, ver
        )
        updatedtrack.img_link_nr = 3
    except IndexError:
        utils.log(3, "musicbrainz tid query failed")
        try:
            updatedtrack = req_mb_track(track, "rid", ver)
            updatedtrack.image = req_album_cover(
                updatedtrack.album_mbid, updatedtrack.image, ver
            )
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
