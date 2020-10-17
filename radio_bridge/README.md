## System Level Dependencies

```bash
# Needed by pyaudio library
sudo apt-get install -y libportaudio2 portaudio19-dev
# Needed for scipy
sudo apt-get install -y libatlas-base-dev # scipy
# Needed if espeak tts implementation is used
sudo apt-get install -y espeak
```

## Cron jobs

### Delete old cached TTS audio files

To speak up subsequent playing of the same text, TTS implementation will cache each synthesized
audio in a file in ``/tmp/tts-audio-cache/`` directory.

Over time, this directory may grow large so you are encouraged to run a periodic cron job which
will delete old cached files.

Keep in mind that cached files can only be re-used if exactly the same text which was already
played before is requested again so long caching periods will be of little use when working with
plugins such as weather and current time one which operate on highly dynamic and changing data.

This cron job will automatically delete cached files older than 4 hours (240 minutes).

```bash
0 */4 * * * find /tmp/tts-audio-cache/ -mmin +240 -print0 | xargs -0 rm
``

## Usage

### Recording custom hello and callsign message using gtts-cli

```bash
gtts-cli -l en-us --slow --nocheck "SIERRA FIVE TWO TANGO ECHO SIERRA TANGO" > audio_files/callsign.mp3
```

## TODO

Main

- [ ] Audit log for all the ran commands
- [ ] Refactor dtmf sequence reader code into main loop and handle cron jobs there
- [ ] Ability to enable and disable TX via GPIO pin when VOX mode is not used
- [ ] Max TX time safe guard - if TX has been on more than X seconds, disable it.
- [ ] Rate limiting / abuse pervention - each command can run x times per time period, depending
  on the command / plugin
- [ ] Move common logging, config parsing code into common pacakge
- [ ] Emulator mode so plugins and functionality can be tested without a radio
- [ ] Ability to enable specific plugins

Plugins:

- [ ] Cron plugin
  - [ ] Say text on specified intervals
- [ ] Weather elsewhere plugin - ability to retrieve weather for other city / station

Misc:

- [ ] Lint (flake8, black, mypy)
