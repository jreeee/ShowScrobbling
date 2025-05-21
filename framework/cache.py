"""
caching to let the MB API have a breather
"""

import os
import json

from framework import utils
from framework import requests


class Cache:
    """cache object to store track metadata"""

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
        """dump data to file"""
        with open(self.cache_fp, "w+", encoding="utf-8") as f:
            f.write(json.dumps(self.cache, indent=4))

    def get_metadata(self, track: utils.Track, track_info_j, ver) -> utils.Track:
        """try to get data from cache, else request and store"""

        # keygen for searching
        mbid_key = False
        if track.mbid != "":
            mbid_key = True
            key = track.mbid
        else:
            key = f"{track.name} -- {track.artist}"

        # searching for song & writing to cache
        if key not in self.cache.keys():
            utils.log(2, "not found in cache")
            if track.image == "":
                new_track = requests.get_cover_image(track, track_info_j, ver)
                track = new_track
                utils.log(2, "got track info")
            if mbid_key:
                self.cache[key] = {
                    "title": track.name,
                    "artist": track.artist,
                    "album_mbid": track.album_mbid,
                    "album": track.album,
                    "length": int(track.length),
                    "cover": track.image,
                }
            else:
                self.cache[key] = {
                    "album": track.album,
                    "length": int(track.length),
                    "cover": track.image,
                }
            utils.log(3, json.dumps(self.cache[key]))
            self.write_cache()
            return track

        # get from json
        updated_track = track
        if mbid_key:
            updated_track.mbid = key
            updated_track.name = self.cache[key]["title"]
            updated_track.artist = self.cache[key]["artist"]
            updated_track.album_mbid = self.cache[key]["album_mbid"]
        # values present for both keys
        updated_track.album = self.cache[key]["album"]
        updated_track.length = int(self.cache[key]["length"])
        updated_track.image = self.cache[key]["cover"]
        updated_track.img_link_nr = 0
        utils.log(3, json.dumps(self.cache[key]))
        return updated_track

    def cache_info(self):
        # get filesize of the current cache file
        cache_size = os.path.getsize(self.cache_fp)
        if cache_size > (1024 * 1024):
            cache_size = str(round(cache_size / (1024 * 1024), 1)) + " MB"
        elif cache_size > 1024:
            cache_size = str(round(cache_size / 1024, 1)) + " KB"
        else:
            cache_size = str(round(cache_size, 1)) + " B"
        print(f"cache file at {self.cache_fp} has a size of {cache_size}")

        entry_base = [0, 0, 0, 0, 0]
        entry_mb = [0, 0, 0, 0, 0]
        # checking for type
        for i in self.cache:
            if " -- " in i:
                entry_base[0] += 1
                tmp = 0
                if self.cache[i]["cover"] == "fallback":
                    entry_base[1] += 1
                    tmp += 4
                if self.cache[i]["album"] == "":
                    entry_base[2] += 1
                    tmp += 2
                if self.cache[i]["length"] == "0":
                    entry_base[3] += 1
                    tmp += 1
                if tmp == 7:
                    entry_base[4] += 1
            else:
                entry_mb[0] += 1
                tmp = 0
                if self.cache[i]["cover"] == "fallback":
                    entry_mb[1] += 1
                    tmp += 4
                if self.cache[i]["album"] == "":
                    entry_mb[2] += 1
                    tmp += 2
                if self.cache[i]["length"] == "0":
                    entry_mb[3] += 1
                    tmp += 1
                if tmp == 7:
                    entry_mb[4] += 1

        print(
            f"Total entries: {entry_base[0] + entry_mb[0]}, Base: {entry_base[0]}, Mbid: {entry_mb[0]}"
        )
        print(
            f"Cover missing: {entry_base[1] + entry_mb[1]}, Base: {entry_base[1]}, Mbid: {entry_mb[1]}"
        )
        print(
            f"Album missing: {entry_base[2] + entry_mb[2]}, Base: {entry_base[2]}, Mbid: {entry_mb[2]}"
        )
        print(
            f"Length missing: {entry_base[3] + entry_mb[3]}, Base: {entry_base[3]}, Mbid: {entry_mb[3]}"
        )
        print(
            f"Garbage Tracks: {entry_base[4] + entry_mb[4]}, Base: {entry_base[4]}, Mbid: {entry_mb[4]}"
        )

        print(entry_base)
        print(entry_mb)

        # for i in self.cache:
        #    if not " -- " in i:
