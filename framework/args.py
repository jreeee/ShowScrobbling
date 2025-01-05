"""
dealing with arguments
"""

import argparse
import constants as const


def parse_args():
    """parsing args and setting default values"""
    parser = argparse.ArgumentParser(
        prog="ShowScrobbling", description="displays your scrobbles on discord"
    )
    parser.add_argument("-u", "--user", nargs="?", help="your lastfm username")
    parser.add_argument(
        "-l",
        "--loglevel",
        nargs="?",
        const=1,
        type=int,
        default=1,
        help="program generated output, 0: silent -> 3: debug, default 1",
    )
    parser.add_argument(
        "-i",
        "--image",
        nargs="?",
        const=1,
        default=const.DEFAULT_TRACK_IMAGE,
        help="default image link if there's none for the track",
    )
    parser.add_argument(
        "-c",
        "--cycle",
        nargs="?",
        const=1,
        type=int,
        default=10,
        help="relevant if track length not found, default = 7, then multiplied by request interval",
    )
    parser.add_argument(
        "-r",
        "--request",
        nargs="?",
        const=1,
        type=int,
        default=30,
        help="interval in seconds to request lastfm api for most recent track, default 30",
    )
    return parser.parse_args()
