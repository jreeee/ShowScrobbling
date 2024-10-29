# Scrobbpy

scrobbpy is yet another discord rich-presence-scrobble-displaying-tool

it checks your lastfm profile for a currently playing song and displays it on discord

why another, are there not enough already?

while there are a good deal of programs out there that do just that, they did not really fit my usecase, leading me to create this one.

scrobbpy aims to be a simple and lightweight cross-platform scrobble-displaying program.

just start the program, enter your lastfm username and it should automatically connect to discord and show which song you are currently listening to. it updates every 30s to fetch the currently playing song

because of its simple design, you can use this on Windows and Linux (probably also Mac) and with any scrobbler as long as it updates your lastfm page somewhat regularly.

## requirements

needs
- urllib
- pypresence

also your lastfm username

TODO for me (jreeee)
- i need to get a discord client id
- a lastfm api key once this repo is public
