# ShowScrobbling

showscrobbling is an inofficial discord rich presence lastfm scrobble displaying app written in python.

it checks your lastfm profile for a currently playing track and displays it on discord.

showscrobbling aims to be simple, lightweight, cross-platform and easy to adapt to fit your needs (if you know a bit of python that is)

just start the program, enter your lastfm username and it should automatically connect to discord and show which song you are currently listening to. it updates every 30s to fetch the currently playing song

because of python, you can use this on Windows and Linux (probably also Mac) and with any scrobbler as long as it updates your lastfm page somewhat regularly.

<img src="https://private-user-images.githubusercontent.com/64651827/381415881-d06b5171-13c4-4a26-aad8-4b0f93bfa8d1.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzAyNjkyOTQsIm5iZiI6MTczMDI2ODk5NCwicGF0aCI6Ii82NDY1MTgyNy8zODE0MTU4ODEtZDA2YjUxNzEtMTNjNC00YTI2LWFhZDgtNGIwZjkzYmZhOGQxLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNDEwMzAlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjQxMDMwVDA2MTYzNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTI3ZTQzMjE1MmEwNThiZGY5M2MxNmM0YTUzNmMwNzA3N2E3YmFjMmUwNzc2NjU5YWNlODEwYWI0ODNjZTYwMGUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.KHLokIdW7eGqmn6aT-hsXKz75NvWws7b19zXdo3aOQE" width="29%" /> <img src="https://private-user-images.githubusercontent.com/64651827/381415943-4c40b6ef-2d0e-4271-8e75-5463f87130c2.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzAyNjkyOTQsIm5iZiI6MTczMDI2ODk5NCwicGF0aCI6Ii82NDY1MTgyNy8zODE0MTU5NDMtNGM0MGI2ZWYtMmQwZS00MjcxLThlNzUtNTQ2M2Y4NzEzMGMyLmpwZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNDEwMzAlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjQxMDMwVDA2MTYzNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWZjMWVjZDMxNjU5NTJhMmMwZDU0ZjU2MjliZWM4MmE4MDNkZTg2MmYzNmE5MWE1MmI1ZTQxZjYyYjEyNjk5YTYmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.BqtPmFfpY3E9m7v79CX-lzki6__jq3dpkGBK8wjOmXU" width="60%" />

when hovering over the icon the playcount is displayed. if the user has the track set as 'loved' this will also be shown here.

when another discord user clicks on your activity, tey'll have two buttons, linking to the song page on lastfm and your profile respectively.

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
-c \| --cycle | 7 | used to calculate track length if not found*
-r \| --request | 30 | interval in seconds to request the lastfm api for most recent track

*currently the api is queried every 30 seconds, since some scrobblers do not correctly transmit when tracks are paused, i decided to implement a very rudimentary cycle approach, that checks how long track are and then gets a cycle count from that. so for a 4 minute track we'd get 9 cycles (8 + 1 "bonus") based off of the request frequency. every request the cycle is decreased. if we land at 0 the song is playing longer than it should and thus has likely been paused. in that case the app sleeps and clears the rpc picture, waking up when a new song is scrobbled. since not all songs have a set length on lastfm there are instances where the app has to "guess" a length. for now this value is set to 7, so roughly a 3.5 to 4 min track, which i feel is reasonable.