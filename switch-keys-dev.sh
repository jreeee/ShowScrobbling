#! /bin/bash

# set -x # debug - just in cases

# i keep my creds in the 'keys' file, like this
# 1st line just contains the lastfm api key, 
# 2nd line contains the lastfm username
# 3rd line contains the discord client id - this will be gone (for good) for the release, once i get a client id that is

KEY_FILE="keys"
PROG_FILE="Scrobb.py"

lfm_api="$(echo $(sed '1!d' "$KEY_FILE"))"
lfm_usr="$(echo $(sed '2!d' "$KEY_FILE"))"
dc_id="$(echo $(sed '3!d' "$KEY_FILE"))"

lfm_api_dummy="lastfm-api-key"
lfm_usr_dummy="lastfm-username"
dc_id_dummy="discord-client-id"

add_keys() {
    sed -i --follow-symlinks "s/${lfm_api_dummy}/${lfm_api}/" "$PROG_FILE"
    sed -i --follow-symlinks "s/${lfm_usr_dummy}/${lfm_usr}/" "$PROG_FILE"
    sed -i --follow-symlinks "s/${dc_id_dummy}/${dc_id}/" "$PROG_FILE"
}

revert() {
    sed -i --follow-symlinks "s/${lfm_api}/${lfm_api_dummy}/" "$PROG_FILE"
    sed -i --follow-symlinks "s/${lfm_usr}/${lfm_usr_dummy}/" "$PROG_FILE"
    sed -i --follow-symlinks "s/${dc_id}/${dc_id_dummy}/" "$PROG_FILE"
}


case $1 in
    "a" ) add_keys;;
    "r" ) revert;;
    * ) echo "bad arg, 'a' to add keys, 'r' to revert back";;
esac