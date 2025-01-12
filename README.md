# ShowScrobbling
[![pypresence](https://img.shields.io/badge/using-pypresence-00bb88.svg?style=for-the-badge&logo=discord&logoWidth=20)](https://github.com/qwertyquerty/pypresence)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

### description

showscrobbling is an inofficial discord rich presence lastfm scrobble displaying script written in python.

it checks your lastfm profile for a currently playing track and displays it on discord.

### goal

showscrobbling aims to be simple, lightweight, cross-platform and easy to adapt to fit your needs (if you know a bit of python that is)

### why?

i usually listen to music via youtube using [Web Scrobbler](https://web-scrobbler.com/) or local music players like rhythmbox. this means, that i don't have a cool discord rpc to show off my _amazing_ music taste like those spotify peeps, which i wanted to change.

### setup

before starting the programm please execute `setup.py` and enter your username when prompted.
this will create a file called `constats.py` in the framework folder where various static values reside.

### startup

after doing that just start the program, it then should automatically connect to discord and show which song you are currently listening to. it updates every 30s to fetch the currently playing song from lastfm.

because it is written in python, you can use this on Windows and Linux (probably also Mac) and with any scrobbler as long as it updates your lastfm page somewhat regularly.

<img src="media/shsc-profile2.png" width="29%" /> <img src="media/shsc-buttons.jpg" width="60%" />

when hovering over the icon the playcount is displayed. if the user has the track set as 'loved' this will also be shown here.

when another discord user clicks on your activity, they'll have two buttons, linking to the song page on lastfm and your profile respectively.

for linting and formatting the code, the `setup.py` provides a prompt to create a pre-commit hook. this uses `black` for formatting and `pylint` for linting. currently only the formatting has to pass for the commit to be valid and i use pylint more as reference.

## requirements

- python3
- urllib*
- pypresence*

*also present in the ```requirements.txt```

(also your lastfm username and a working internet connection)

## usage

args | default | desc
--- | :---: | ---
-h \| --help | - | displays help message, listing all args
-u \| --user | - | your lastfm username 
-l \| --loglevel | 1 | program generated output, 0: silent -> 3: debug, default 1
-i \| --image | [this](https://media.tenor.com/Hro804BGJaQAAAAj/miku-headbang.gif) | default image link if there's none for the track
-c \| --cycle | 10 | used to calculate track length if not found*
-r \| --request | 30 | interval in seconds to request the lastfm api for most recent track

*currently the api is queried every 30 seconds, since some scrobblers do not correctly transmit when tracks are paused, i decided to implement a very rudimentary cycle approach, that checks how long track are and then gets a cycle count from that. so for a 4 minute track we'd get 9 cycles (8 + 1 "bonus") based off of the request frequency. every request the cycle is decreased. if we land at 0 the song is playing longer than it should and thus has likely been paused. in that case the script sleeps and clears the rpc picture, waking up when a new song is scrobbled. since not all songs have a set length on lastfm there are instances where the script has to "guess" a length. for now this value is set to 10, so roughly a 5 to 5.5 min track, after which the program will 'sleep'.