"""
dealing with arguments
"""

import argparse
import framework.constants as const


def int_min(arg):
    """ensure that the lfm api isn't bombarded with requests"""
    try:
        i = int(arg)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("request interval must me int") from exc
    if int(const.MIN_QRY_INT) > i:
        raise argparse.ArgumentTypeError(
            f"request interval must be at least {const.MIN_QRY_INT}"
        )
    return i


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
        "-r",
        "--request",
        nargs="?",
        const=1,
        type=int_min,
        default=30,
        help="interval in seconds to request lastfm api for most recent track, default 30",
    )
    return parser.parse_args()
