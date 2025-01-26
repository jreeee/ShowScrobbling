"""
util functions and data types
"""

GLOBAL_LOG_LEVEL = 1


def log(loglevel, content):
    """simple logging"""
    if loglevel <= GLOBAL_LOG_LEVEL:
        print(content)


class Track:
    """basic Track object"""

    artist = name = image = url = mbid = album = album_mbid = ""
    length = 0
