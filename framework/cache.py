"""
caching to let the MB API have a breather
"""

import os
import json
import time

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
            # link entry
            if key in self.cache.keys() and self.cache[key].get("mbid") is not None:
                key = self.cache[key]["mbid"]
                mbid_key = True

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

    def merge_entries(self, key_basic, key_mbid, prefer_mbid_data=True) -> None:
        """merging basic type track into mbid type track and generating a link type"""
        # usually MB data is more accurate
        if prefer_mbid_data:
            preferred_data = self.cache[key_mbid]
            backup_data = self.cache[key_basic]
        else:
            preferred_data = self.cache[key_basic]
            backup_data = self.cache[key_mbid]

        # merging using preferred data and writing that to the mbid entry
        track_cover = (
            preferred_data["cover"]
            if preferred_data["cover"] in ("", "fallback")
            else backup_data["cover"]
        )
        track_length = (
            preferred_data["length"]
            if preferred_data["length"] == 0
            else backup_data["length"]
        )
        track_album = (
            preferred_data["album"]
            if preferred_data["album"] == ""
            else backup_data["album"]
        )

        # write values to mbid track
        self.cache[key_mbid]["cover"] = track_cover
        self.cache[key_mbid]["length"] = track_length
        self.cache[key_mbid]["album"] = track_album

        # remove values from basic track and convert to link
        link = {key_basic: {"mbid": key_mbid}}
        print(link)
        self.cache.update(link)

    def cache_info(self):
        """display info about the cahe file"""

        # TODO split into smaller functions, add log instead of print

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
        entry_l = 0
        # checking for type
        for i in self.cache:
            if " -- " in i:
                if self.cache[i].get("mbid") is not None:
                    entry_l += 1
                else:
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
            f"Total entries: {entry_b[0] + entry_mb[0] + entry_l}, Base: {entry_b[0]}, Mbid: {entry_mb[0]}, Link: {entry_l}"
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

        # find_dulicates(self)
        # find identical tracks in both formats
        # ideally: merge into mbid, replace basic with link to mbid
        for i in self.cache:
            # basic tracks, disregard link types
            if " -- " in i and self.cache[i].get("mbid") is None:
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
                            print("> MERGING")
                            self.merge_entries(i, j)
        # update cache
        self.write_cache()

        # check album mbids and add a cover? could be useful for new songs to not even qry covers
        track_album_mbids = []

        # find missing covers
        for i in self.cache:
            if not " -- " in i:
                # a_mbid = self.cache[i]["album_mbid"]
                # a_cover = self.cache[i]["cover"]
                # for j in self.cache:
                #     if not " -- " in j and j != i:
                #         if (
                #             a_mbid == self.cache[j]["album_mbid"]
                #             and a_cover == "fallback"
                #         ):
                #             print("---------------------")
                #             print(self.cache[j])
                #             print(self.cache[i])
                #             print("---------------------")
                if self.cache[i]["cover"] == "fallback":
                    if self.cache[i]["album_mbid"] not in track_album_mbids:
                        track_album_mbids.append(self.cache[i]["album_mbid"])

        track_album_covers = [""] * len(track_album_mbids)
        # check if in cache
        for i in self.cache:
            if not " -- " in i:
                if self.cache[i]["cover"] != "fallback":
                    tmp_mbid = self.cache[i]["album_mbid"]
                    if tmp_mbid in track_album_mbids:
                        track_album_covers[track_album_mbids.index(tmp_mbid)] = (
                            self.cache[i]["cover"]
                        )

        print(f"list: {track_album_mbids}")
        print(f"list: {track_album_covers}")

        for i in range(0, len(track_album_mbids), 1):
            if track_album_covers[i] == "":
                print(f"> getting cover for mbid item [{i+1}/{len(track_album_mbids)}]")
                # TODO fix version
                track_album_covers[i] = requests.req_album_cover(
                    track_album_mbids[i], "", 1.9
                )
                time.sleep(2)

        entries_updated = 0
        for i in self.cache:
            if not " -- " in i:
                if self.cache[i]["cover"] == "fallback":
                    tmp_mbid = self.cache[i]["album_mbid"]
                    if tmp_mbid in track_album_mbids:
                        entries_updated += 1
                        self.cache[i]["cover"] = track_album_covers[
                            track_album_mbids.index(tmp_mbid)
                        ]

        self.write_cache()

        print(f"updated {entries_updated} entries")

        print(f"list: {track_album_mbids}")
        print(f"list: {track_album_covers}")
