"""
functions related to API queries
"""

import urllib.request
import json

from framework import utils
from framework import constants as const


def get_json(url):
    """return json object for given url"""
    url_obj = urllib.request.urlopen(url)
    if url_obj.getcode() == 404:
        utils.log(2, "no site")
        return None
    url_decoded = url_obj.read().decode()
    json_obj = json.loads(url_decoded)
    utils.log(3, json.dumps(json_obj, indent=2))
    return json_obj


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
