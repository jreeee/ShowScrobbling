import os
import json

from framework import utils
from framework import requests


class Cache:
    cache = {}
    cache_fp = ""

    def __init__(self, cache_fp):
        self.cache_fp = cache_fp
        cache_dir = os.path.dirname(self.cache_fp)
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        if os.path.exists(self.cache_fp):
            with open(self.cache_fp, "r", encoding="utf-8") as f:
                self.cache = json.loads(f.read())
        else:
            self.write_cache()

    def write_cache(self):
        with open(self.cache_fp, "w+", encoding="utf-8") as f:
            f.write(json.dumps(self.cache, indent=4))

    def get_metadata(self, track: utils.Track, track_info_j, VERSION) -> utils.Track:
        # keygen for searching
        mbid_key = False
        if track.mbid != "":
            mbid_key = True
            key = track.mbid
        else:
            key = f"{track.name} -- {track.artist}"

        # searching for song & writing to cache
        if key not in self.cache.keys():
            utils.log(2, "not found in cache, querying for track info")
            new_track = requests.get_cover_image(track, track_info_j, VERSION)
            utils.log(2, "got track info")
            if mbid_key:
                self.cache[key] = {
                    "title": new_track.name,
                    "artist": new_track.artist,
                    "album_mbid": new_track.album_mbid,
                    "album": new_track.album,
                    "length": new_track.length,
                    "cover": new_track.image,
                }
            else:
                self.cache[key] = {
                    "album": new_track.album,
                    "length": new_track.length,
                    "cover": new_track.image,
                }
            utils.log(3, json.dumps(self.cache[key]))
            self.write_cache()
            return new_track

        # get from json
        updated_track = track
        if mbid_key:
            updated_track.mbid = key
            updated_track.name = self.cache[key]["title"]
            updated_track.artist = self.cache[key]["artist"]
            updated_track.album_mbid = self.cache[key]["album_mbid"]
        # values present for both keys
        updated_track.album = self.cache[key]["album"]
        updated_track.length = self.cache[key]["length"]
        updated_track.image = self.cache[key]["cover"]
        utils.log(3, json.dumps(self.cache[key]))
        return updated_track
