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
        if key not in self.cache.keys() or self.cache[key]["cover"] == "fallback":
            utils.log(2, "not found in cache")
            if track.image in ("", "fallback"):
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
        """display info about the cahe file"""

        # get filesize of the current cache file
        cache_size = os.path.getsize(self.cache_fp)
        if cache_size > (1024 * 1024):
            cache_size = str(round(cache_size / (1024 * 1024), 1)) + " MB"
        elif cache_size > 1024:
            cache_size = str(round(cache_size / 1024, 1)) + " KB"
        else:
            cache_size = str(round(cache_size, 1)) + " B"
        print(f"cache file at {self.cache_fp} has a size of {cache_size}")

        entry_b = [0, 0, 0, 0, 0]
        entry_mb = [0, 0, 0, 0, 0]
        # checking for type
        for i in self.cache:
            if " -- " in i:
                entry_b[0] += 1
                tmp = 0
                if self.cache[i]["cover"] == "fallback":
                    entry_b[1] += 1
                    tmp += 4
                if self.cache[i]["album"] == "":
                    entry_b[2] += 1
                    tmp += 2
                if self.cache[i]["length"] == "0":
                    entry_b[3] += 1
                    tmp += 1
                if tmp == 7:
                    entry_b[4] += 1
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
            f"Total entries: {entry_b[0] + entry_mb[0]}, Base: {entry_b[0]}, Mbid: {entry_mb[0]}"
        )
        print(
            f"Cover missing: {entry_b[1] + entry_mb[1]}, Base: {entry_b[1]}, Mbid: {entry_mb[1]}"
        )
        print(
            f"Album missing: {entry_b[2] + entry_mb[2]}, Base: {entry_b[2]}, Mbid: {entry_mb[2]}"
        )
        print(
            f"Length missing: {entry_b[3] + entry_mb[3]}, Base: {entry_b[3]}, Mbid: {entry_mb[3]}"
        )
        print(
            f"Garbage Tracks: {entry_b[4] + entry_mb[4]}, Base: {entry_b[4]}, Mbid: {entry_mb[4]}"
        )

        print(entry_b)
        print(entry_mb)

        # find identical tracks in both formats
        # ideally: merge into mbid, replace basic with link to mbid
        for i in self.cache:
            # basic tracks
            if " -- " in i:
                title, artist = i.split(" -- ")
                for j in self.cache:
                    # mbid tracks
                    if not " -- " in j:
                        if (
                            self.cache[j]["title"] == title
                            and self.cache[j]["artist"] == artist
                        ):
                            print("found match for " + artist + " - " + title)
                            print("---------------------")
                            print(self.cache[j])
                            print(self.cache[i])
                            print("---------------------")

        # check album mbids and add a cover? could be useful for new songs to not even qry covers
        for i in self.cache:
            if not " -- " in i:
                a_mbid = self.cache[i]["album_mbid"]
                a_cover = self.cache[i]["cover"]
                for j in self.cache:
                    if not " -- " in j and j != i:
                        if (
                            a_mbid == self.cache[j]["album_mbid"]
                            and a_cover == "fallback"
                        ):
                            print("---------------------")
                            print(self.cache[j])
                            print(self.cache[i])
                            print("---------------------")
