#! /usr/bin/env python

"""
ShowScrobbling
a small-ish python script that uses Pypresence and last.fm (and MusicBrainz)
to display coverart of your currently scrobbling song in Discord
"""

# system libraries
import sys
import os
import time
import traceback

# external libraries


# check pypresence ActivityType support
try:
    from pypresence import Presence
    from pypresence import exceptions as ex
    from pypresence import ActivityType

    ACTIVITY_TYPE_SUPPORT = True
except (ImportError, ModuleNotFoundError):
    try:
        from lynxpresence import Presence
        from lynxpresence import ActivityType
        import lynxpresence.exceptions as ex

        ACTIVITY_TYPE_SUPPORT = True
    except ModuleNotFoundError:
        ACTIVITY_TYPE_SUPPORT = False

# local project files
from framework import args as parser
from framework import constants as const
from framework import utils
from framework import requests
from framework import cache

# -----------------------------------------------------------

VERSION = "1.9"

# get and parse args
args = parser.parse_args()

# setting vars
if args.user is not None:
    LFM_USR = args.user
else:
    LFM_USR = const.USR
if args.loglevel != 1:
    utils.GLOBAL_LOG_LEVEL = args.loglevel
if args.strictness is None or len(args.strictness) == 0:
    args.strictness = [5, 6, 7]

# -----------------------------------------------------------


class Scrobbpy:
    """script object"""

    track = utils.Track
    rpc_state = utils.RpcState
    progcache: cache.Cache

    # rpc setup
    def __init__(self, client_id):
        if self.other_is_running():
            utils.log(1, "other instance already running.")
            sys.exit(1)
        utils.log(1, "init rpc")
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.rpc_connected = True
        self.rpc_state = utils.RpcState()
        utils.log(1, f"init finished, running version {VERSION}")
        # TODO improve / expand to local paths
        fp = os.path.expanduser(args.cache_path)
        utils.log(3, f"cache file @ {fp}")
        self.progcache = cache.Cache(fp)

    # rpc cleanup
    def __del__(self):
        try:
            if self.rpc is not None and self.rpc_connected:
                self.rpc.clear()
                self.rpc.close()
        except AttributeError:
            utils.log(2, "rpc attribute missing")
        utils.log(1, "rpc object deleted")

    def other_is_running(self):
        """check if another instance is already running"""
        pid = os.getpid()
        utils.log(3, f"PID: {pid}")
        # Unix like
        if os.name != "nt":
            return (
                "python"
                in os.popen(f"ps aux | grep showscrobbling.py | grep -v {pid}").read()
            )
        # Windows
        else:
            import subprocess

            win_bs = [
                "powershell.exe",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | "
                "Select-Object CommandLine,ProcessId | "
                "Where-Object {$_.CommandLine -like '*showscrobbling.py*'} | "
                "Select-Object -ExpandProperty ProcessId",
            ]
            ps = subprocess.run(win_bs, capture_output=True, text=True, shell=True)
            procs = ps.stdout.splitlines()
            utils.log(3, ps)
            return len(procs) > 1

    def sleep(self):
        """zzzzzzzzz"""
        # all of the following things need to be set just once for a given sleep period
        if not self.rpc_state.sleeping:
            self.rpc.clear()
            self.rpc_state.sleeping = True
            utils.log(1, "no song playing, sleeping")

    # anything with _j is a json object
    def update(self):
        """called every interval to check the current status"""

        # query lastfm for the most recent track
        recent_track_j = requests.get_json(const.URL_RECENT_TRACK)

        # get recent track info
        playing = recent_track_j["recenttracks"]["track"][0].get("@attr", {})
        if len(playing) == 0:
            self.sleep()
            return
        # i don't think this is necessary, but better safe than sorry
        key, value = next(iter(playing.items()))
        if not (key == "nowplaying" and value == "true"):
            self.sleep()
            return

        new_url = recent_track_j["recenttracks"]["track"][0]["url"]

        # in case of new track
        if new_url != self.track.url:
            # update states
            self.rpc_state.update(args.request)
            # create new track object
            self.track = utils.Track(recent_track_j, args.enable_lfm_track_img)
            self.track.url = new_url
            # query lfm for track info
            data_track_url = requests.track_info_url(recent_track_j)
            track_info_j = requests.get_json(data_track_url)
            # get remaining data from cache / requests
            self.track = self.progcache.get_metadata(
                self.track, track_info_j, VERSION, args.strictness
            )
            if self.track.image == "fallback":
                self.track.image = const.DEFAULT_TRACK_IMAGE
                utils.log(3, f"using default track image {self.track.image}")

        if not self.rpc_state.new_track:
            return

        # create new track rpc
        self.rpc_state.new_track = False

        # store args in dict to only include valid ones:
        # TODO buttons: what happens if the lfm link is invalid?
        update_args = {
            "details": utils.create_detail_text(self.track, ACTIVITY_TYPE_SUPPORT),
            "start": self.rpc_state.start_time,
            "state": utils.create_state_text(self.track),
            "large_image": self.track.image,
            "large_text": utils.create_hover_text(
                track_info_j, self.track, ACTIVITY_TYPE_SUPPORT
            ),
            "small_text": "scrobbling songs",  # does this even do anything?
            "buttons": [
                {
                    "label": "song on last.fm",
                    "url": self.track.url,
                },
                {
                    "label": f"{LFM_USR}'s profile"[0:31],
                    "url": f"https://www.last.fm/user/{LFM_USR}",
                },
            ],
        }

        if int(self.track.length) != 0:
            update_args["end"] = (
                int(self.rpc_state.start_time) + int(self.track.length) / 1000
            )

        self.rpc.clear()
        try:
            if ACTIVITY_TYPE_SUPPORT:
                self.rpc.update(activity_type=ActivityType.LISTENING, **update_args)
            else:
                self.rpc.update(**update_args)
            info = f"▶️ {self.track.name}, {self.track.artist}, {self.track.listens}"
            if utils.GLOBAL_LOG_LEVEL > 1:
                info = f"{info}, img: {self.track.img_link_nr}"
            utils.log(1, info)
        # handle exceptions
        except (ex.ServerError, ex.ResponseTimeout, ex.PipeClosed) as e:
            utils.throw_error(e)


# -----------------------------------------------------------


def main():
    """main method for ShowScrobbling"""
    try:
        if rpc := Scrobbpy(const.CLIENT_ID):
            if args.check_cache:
                rpc.progcache.check_cache(args.strictness, VERSION)
                del rpc
                sys.exit(0)
            while True:
                try:
                    rpc.update()
                except Exception as e:
                    utils.log(1, str(e) + " occurred in " + traceback.format_exc())
                    utils.log(1, f"trying again in {args.request}s")
                time.sleep(args.request)
    except ConnectionRefusedError:
        utils.log(1, "connection refused - is discord running?")
    except KeyboardInterrupt:
        utils.log(1, "exiting")
        del rpc
        sys.exit(0)


if __name__ == "__main__":
    main()
