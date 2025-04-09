> [v1.0](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.0) [24-10-30] - the first _proper_ version:

the project has been renamed from **Scrobbpy** to **ShowScrobbling** ~~very catchy, i know~~

- added a short description to the readme
- added requirements in the readme and `requirements.txt`
- added args and explanation to the readme
- added a unique discord id to the script ([#1](https://github.com/jreeee/ShowScrobbling/issues/1))

full changelog: [v0.0...v1.0](https://github.com/jreeee/showscrobbling/compare/v0.0...v1.0)

> [v1.1](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.1) [25-01-02] - officially 
licensed

- fixed several bugs, better error handling
- added black formatting for the code
- added MIT license
- added pypresence & code style badges to readme
- added images to readme

full changelog: [v1.0...v1.1](https://github.com/jreeee/showscrobbling/compare/v1.0...v1.1)

> [v1.2](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.2) [25-01-05] - setting up properly

⚠️ added `setup.py` that should be executed once before starting showscrobbling

- split showscrobbling into multiple files for better maintainability and greater flexibility when developing

full changelog: [v1.1...v1.2](https://github.com/jreeee/showscrobbling/compare/v1.1...v1.2)

> [v1.3](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.3) [25-01-12] - completing (old) TODOs

- fixed shebang: `./shoscro.py` now works instead of just `python shoscro.py`
- fixed cover not being displayed when getting lfm errors ([#11](https://github.com/jreeee/ShowScrobbling/issues/11))
- removed unecessary variable `LFM_TR_IN_QRY` from `constants.py`
- rewrote the readme ([#3](https://github.com/jreeee/ShowScrobbling/issues/3))
- figured how i want to approach formatting & linting ([#2](https://github.com/jreeee/ShowScrobbling/issues/2))

full changelog: [v1.2...v1.3](https://github.com/jreeee/showscrobbling/compare/v1.2...v1.3)

> [v1.4](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.4) [25-01-13] - good night

- replaced the cycle mechanic with _nowplaying_ attribute combined with a sleep function
- finished up old TODOs ([#4](https://github.com/jreeee/ShowScrobbling/issues/4))

full changelog: [v1.3...v1.4](https://github.com/jreeee/showscrobbling/compare/v1.3...v1.4)

> [v1.5](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.5) [25-01-14] - cleanup

- fixed activity showing the wrong hover message under certain condtions
- fixed activity sometimes not showing ([#8](https://github.com/jreeee/ShowScrobbling/issues/8))
- added better install instructions to the readme
- removed unused cycle argument

full changelog: [v1.4...v1.5](https://github.com/jreeee/showscrobbling/compare/v1.4...v1.5)

> [v1.6](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.6) [25-02-08] - refactoring

🔧 dev: the pre-commit hook has been updated, `rm .git/hooks/pre-commit && setup.py` to get the updated one.

- 🔧 pre-commit now checks that readme- and script version numbers match

- improved RPC error handling
- fixed song button having the link of the previous song instead of the current one
- changed `setup.py` to use multiline strings for easier development
- added version & license badge to the readme
- refactored / restructured code, merged _refactor_ ([#14](https://github.com/jreeee/ShowScrobbling/pull/14)), closing ([#13](https://github.com/jreeee/ShowScrobbling/issues/13))
- ~~discord messed up lol ([#12](https://github.com/jreeee/ShowScrobbling/issues/12))~~

full changelog: [v1.5...v1.6](https://github.com/jreeee/showscrobbling/compare/v1.5...v1.6)

> [v1.7](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.7) [25-02-25] - caching in

⚠️please re-run `setup.py` to update your `constants.py`

songs are now being cached. by default the file is going to be saved to the user's home directory as `~/.cache/showscrobbling/metadata.json`. this can be configured using `-c path/to/location` otherwise the `CACHE_PATH` variable in `constants.py` will be used.
Updating via `setup.py` now also carries over the `DEFAULT_TRACK_IMAGE` from the old file to the new one.

- better error handling
- added option to update lfm's recent track image using "-E" see [#15](https://github.com/jreeee/ShowScrobbling/issues/15)
- added caching, merged cache branch ([#16](https://github.com/jreeee/ShowScrobbling/pull/16)), closing ([#7](https://github.com/jreeee/ShowScrobbling/issues/7))

full changelog: [v1.6...v1.7](https://github.com/jreeee/showscrobbling/compare/v1.6...v1.7)

> [v1.8](https://github.com/jreeee/ShowScrobbling/releases/tag/v1.8) [25-03-20] - ActivityType support is finally here!

for pyprence to display the activitity as "Listening to" instead of "Playing" you'll need either the git version of pypresence or lynxpresence instead.

- added a logo (square and circle)
- added updated screenshots, updated readme to reflect changes
- reworked activity text
- now displaying song length: merged _next_ ([#18](https://github.com/jreeee/ShowScrobbling/pull/18)), closing ([#5](https://github.com/jreeee/ShowScrobbling/issues/5))

full changelog: [v1.7...v1.8](https://github.com/jreeee/showscrobbling/compare/v1.7...v1.8)
