# Scrobbpy
horrible python code

needs urllib and pypresence
also your lastfm username and api key for this application

also i need to get a discord app id

scrobbpy is yet another discord rich presence scrobble displaying tool

why another, are there not enough already?
- while there are a good deal of programs out there that do just that, they all had some drawbacks, leading me to create this one.

scrobbpy aims to be a simple and lightweight cross platform scrobble-displaying program.

the way it works is the following: get the api key for your username on lastfm [TODO: add link], and start the script.

it will query the lastfm website every 30s to see what you are listening to. it then takes the info about the track it got back and uses pypresence to create a discord activity. and that's basically it.

because of its simple design, you can use this on Windows and Linux (probably also Mac) and with any scrobbler as long as it updates your lastfm page somewhat regularly.

[TODO: rwerite a bit more structured and nicer looking]