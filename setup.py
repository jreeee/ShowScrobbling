#! /usr/bin/env python

# pylint: skip-file

import os
import stat
import sys
from pathlib import Path

# get absolute path to the framework dir to create the constants file
SCRIPT_DIR = Path(__file__).resolve().parent

# create constants.py
CONST_FILE = SCRIPT_DIR / "framework" / "constants.py"

username = ""

if CONST_FILE.exists():
    res = input("const file already present. [o]verride / [u]pdate / [e]xit: ")
    if res == "o" or res == "override":
        username = input("please enter your lastfm username: ")
    elif res == "u" or res == "update":
        # get and use the existing username
        import framework.constants
        username = framework.constants.USR
    else:
        print("exting")
        sys.exit(0)
else:
    username = input("please enter your lastfm username: ")

CONST_CONTENT =f"""\
# pylint: skip-file

# the following values can be changed
USR = "{username}"
DEFAULT_TRACK_IMAGE = "https://media.tenor.com/Hro804BGJaQAAAAj/miku-headbang.gif"

# don't change the following values if you want the script to work properly
LFM_API_KEY = "5125b622ac7cb502b9a857bb59a57830"
MB_REC_QRY = "https://musicbrainz.org/ws/2/recording/?query="

CLIENT_ID = "1301054835101270117"
URL_RECENT_TRACK = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying="true"&user={{USR}}&limit=1&api_key={{LFM_API_KEY}}&format=json'
URL_TRACK_INFO = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={{LFM_API_KEY}}&username={{USR}}'
MIN_QRY_INT = 15
"""
with open(CONST_FILE, "w", encoding='utf-8') as constants:
    constants.write(CONST_CONTENT)

# create git pre-commit hook file, requires bash to be installed
res = input("create pre-commit hook file?[y/N]: ")

if res != "Y" and res != "y":
    print("setup complete, exting")
    sys.exit(0)

HOOK_FILE = SCRIPT_DIR / ".git" / "hooks" / "pre-commit"


HOOK_CONTENT = """\
#! /bin/bash

onfail () {
    echo "ERROR: pre-commit hook failed, $1" && exit 1;
}

echo "pre-commit checks:"
echo "- version check:"
readme_v="$(echo $(sed -nE 's/.*VERSION-([0-9.]+).*/\\1/p' README.md))"
script_v="$(echo $(sed -nE 's/.*VERSION = \"([0-9.]+)\"/\\1/p' showscrobbling.py))"
[[ $readme_v != $script_v ]] && onfail "inconsistent versions readme: $readme_v, script: $script_v"

echo "- black check:" && black --force-exclude="setup.py" --check .
if [ $? -ne 0 ]; then
    echo "- black formatting:" && black --force-exclude="setup.py" --verbose .
    onfail "missing files were formatted, please add them"
fi
echo "- pylint" && pylint .

echo "All checks passed."
"""

with open(HOOK_FILE, "w", encoding='utf-8') as hooks:
    hooks.write(HOOK_CONTENT)

# make file executable works for linux & mac afaik
perm = os.stat(HOOK_FILE).st_mode
os.chmod(HOOK_FILE, perm | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
print("successfully created pre-commit hook")