"""
caching to let the MB API have a breather
"""

import os
import json
import time

from framework import utils
from framework import apirqs


class Cache:
    """cache object to store track metadata"""

    cache = {}
    cache_fp = ""

    def __init__(self, cache_fp):
        # assume fp points to metadata.json
        self.cache_fp = cache_fp
        # pointed to the dir in which metadata.json lies
        if os.path.isdir(cache_fp):
            self.cache_fp = os.path.join(cache_fp, "metadata.json")
        # create dirs if not present
        os.makedirs(os.path.dirname(self.cache_fp), exist_ok=True)
        # write empty json if not present
        if not os.path.exists(self.cache_fp):
            self.write_cache()
        # open cache to read
        with open(self.cache_fp, "r", encoding="utf-8") as f:
            self.cache = json.loads(f.read())

    def write_cache(self):
        """dump data to file"""
        with open(self.cache_fp, "w+", encoding="utf-8") as f:
            f.write(json.dumps(self.cache, indent=4))

    def entry_status(self, entry) -> []:
        """check entry from cache for missing things"""

        status = [1, 0, 0, 0, 0]
        if entry.get("mbid") is None:
            status[1] = 1 if entry["cover"] == "fallback" else 0
            status[2] = 1 if entry["album"] == "" else 0
            status[3] = 1 if entry["length"] == "0" else 0
            # calculate and store bitmask
            status[4] = 4 * status[1] + 2 * status[2] + status[3]
        return status

    def get_metadata(
        self, track: utils.Track, track_info_j, ver, strictness
    ) -> utils.Track:
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
                new_track = apirqs.get_cover_image(track, track_info_j, ver)
                track = new_track
                utils.log(2, "got track info")

            if mbid_key:
                track_data = {
                    "title": track.name,
                    "artist": track.artist,
                    "album_mbid": track.album_mbid,
                    "album": track.album,
                    "length": int(track.length),
                    "cover": track.image,
                }
            else:
                track_data = {
                    "album": track.album,
                    "length": int(track.length),
                    "cover": track.image,
                }
            utils.log(3, json.dumps(track_data))

            if self.entry_status(track_data)[4] not in strictness:
                self.cache[key] = track_data
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

        # usually the MB data is more accurate
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
        # ! this might be problematic since we change the dict while iterating over it !
        link = {key_basic: {"mbid": key_mbid}}
        utils.log(2, link)
        self.cache.update(link)

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
        utils.log(1, f"cache file at {self.cache_fp} has a size of {cache_size}")

    def check_entries(self, ent_type, strictness) -> []:
        """
        check how many entries are missing what. strictness is an int array,
        calculated by the following metric:
        no cover +4, no album +2, no length +1
        so the lowest strictness is 7, where only tracks without any data are discarded.
        type is either 'base', 'mb' or 'link' which checks the different formats
        """

        entries = [0, 0, 0, 0, 0]
        for i in self.cache:
            # checking for type
            if ent_type in ["base", "link"]:
                if " -- " in i:
                    if ent_type == "link":
                        if self.cache[i].get("mbid") is not None:
                            entries[0] += 1
                    else:
                        if self.cache[i].get("mbid") is None:
                            tmp = self.entry_status(self.cache[i])
                            tmp[4] = 1 if tmp[4] in strictness else 0
                            entries = [sum(x) for x in zip(entries, tmp)]

            elif ent_type == "mb":
                if not " -- " in i:
                    tmp = self.entry_status(self.cache[i])
                    tmp[4] = 1 if tmp[4] in strictness else 0
                    entries = [sum(x) for x in zip(entries, tmp)]

        utils.log(3, entries)
        return entries

    def find_duplicates(self):
        """find identical tracks in both formats, merge into mbid,
        replace basic entry with link to mbid"""
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
                            utils.log(1, "found match for " + artist + " - " + title)
                            utils.log(2, "---------------------")
                            utils.log(2, self.cache[j])
                            utils.log(2, self.cache[i])
                            utils.log(2, "---------------------")
                            utils.log(1, "> MERGING")
                            self.merge_entries(i, j)
        # update cache
        self.write_cache()

    def check_album_mbid_cover_qry(self, version):
        """check album mbids and add a cover"""
        track_album_mbids = []

        # find mbid entries with missing covers
        for i in self.cache:
            if not " -- " in i:
                if self.cache[i]["cover"] == "fallback":
                    if self.cache[i]["album_mbid"] not in track_album_mbids:
                        track_album_mbids.append(self.cache[i]["album_mbid"])

        if len(track_album_mbids) == 0:
            return
        # new array to hold the links wth the same size as the mbid array
        track_album_covers = [""] * len(track_album_mbids)
        # check if already in cache
        for i in self.cache:
            if not " -- " in i:
                if self.cache[i]["cover"] != "fallback":
                    tmp_mbid = self.cache[i]["album_mbid"]
                    if tmp_mbid in track_album_mbids:
                        track_album_covers[track_album_mbids.index(tmp_mbid)] = (
                            self.cache[i]["cover"]
                        )

        utils.log(3, f"list: {track_album_mbids}")
        utils.log(3, f"list: {track_album_covers}")

        for i in range(0, len(track_album_mbids), 1):
            if track_album_covers[i] == "":
                print(f"> getting cover for mbid item [{i+1}/{len(track_album_mbids)}]")
                track_album_covers[i] = apirqs.req_album_cover(
                    track_album_mbids[i], "", version
                )
                time.sleep(2)

        utils.log(3, f"list: {track_album_mbids}")
        utils.log(3, f"list: {track_album_covers}")

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

        utils.log(1, f"updated {entries_updated} entries")

    def remove_garbage_entries(self, strictness):
        """remove entries based on strictness"""

        updated_cache = {}
        for i in self.cache:
            status = self.entry_status(self.cache[i])
            if status[4] not in strictness:
                updated_cache[i] = self.cache[i]
        self.cache = updated_cache
        self.write_cache()

    def check_cache(self, strictness, version):
        """check and clean up cache"""

        self.cache_info()
        self.find_duplicates()
        ent_base = self.check_entries("base", strictness)
        ent_mb = self.check_entries("mb", strictness)
        ent_link = self.check_entries("link", strictness)

        utils.log(
            1,
            f"Total entries: {ent_base[0] + ent_mb[0] + ent_link[0]}\
 - base: {ent_base[0]}, mb: {ent_mb[0]}, link: {ent_link[0]}",
        )
        num_strict_entries = ent_base[4] + ent_mb[4]
        utils.log(
            1,
            f"Entries matching strictness: {num_strict_entries}\
 - base: {ent_base[4]}, mb: {ent_mb[4]}",
        )

        self.check_album_mbid_cover_qry(version)
        if num_strict_entries == 0:
            return
        a = input(
            f"> remove {num_strict_entries} entries based on strictness {strictness}? [y/N]"
        )
        if a in ["Y", "y", "Yes", "yes"]:
            self.remove_garbage_entries(strictness)
            utils.log(
                1, f"Removed all {num_strict_entries} entries matching strictness"
            )
