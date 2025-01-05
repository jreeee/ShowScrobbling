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

if CONST_FILE.exists():
    res = input("const file already present. overwrite?[y/N]: ")
    if res != "Y" and res != "y":
        print("exting")
        sys.exit(0)
    else:
        open(CONST_FILE, "w", encoding='utf-8').close()

USERNAME = input("please enter your lastfm username: ")

with open(CONST_FILE, "w", encoding='utf-8') as constants:
    constants.write("# pylint: skip-file")
    constants.write("# the following values can be changed\n")
    constants.write(f'USR = "{USERNAME}"\n')
    constants.write('DEFAULT_TRACK_IMAGE = "https://media.tenor.com/Hro804BGJaQAAAAj/miku-headbang.gif"\n')
    constants.write("\n# the following values shouldn't be changed\n")
    constants.write('LFM_API_KEY = "5125b622ac7cb502b9a857bb59a57830"\n')
    constants.write('LFM_TR_IN_QRY = "http://ws.audioscrobbler.com/2.0/?method=track.getInfo"\n')
    constants.write('MB_REC_QRY = "https://musicbrainz.org/ws/2/recording/?query="\n\n')
    constants.write('CLIENT_ID = "1301054835101270117"\n')
    constants.write("URL_RECENT_TRACK = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&nowplaying=\"true\"&user={USR}&limit=1&api_key={LFM_API_KEY}&format=json'\n")
    constants.write("URL_TRACK_INFO = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={LFM_API_KEY}&username={USR}'\n")

# create git pre-commit hook file
HOOK_FILE = SCRIPT_DIR / ".git" / "hooks" / "pre-commit"


res = input("create pre-commit hook file?[y/N]: ")
if res != "Y" and res != "y":
    print("exting")
    sys.exit(0)

with open(HOOK_FILE, "w", encoding='utf-8') as hooks:
    hooks.write("#!/bin/bash\n\n")
    hooks.write('echo "pre-commit checks:"')
    hooks.write('echo "- running black" && black --force-exclude="setup.py" --verbose .\n')
    hooks.write("if [ $? -ne 0 ]; then\n")
    hooks.write('    echo "Pre-commit hook failed. Please fix the issues and try again."\n')
    hooks.write("    exit 1\n")
    hooks.write("fi\n")
    hooks.write('echo "- running pylint" && pylint .\n\n')
    hooks.write('echo "All checks passed."\n')

# work only for linux & mac afaik but is also optional
perm = os.stat(HOOK_FILE).st_mode
os.chmod(HOOK_FILE, perm | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
