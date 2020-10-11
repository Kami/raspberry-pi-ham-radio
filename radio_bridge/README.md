## System Level Dependencies

```bash
sudo apt-get install libatlas-base-dev # scipy
```

## Cron jobs

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

Plugins:

- [ ] Cron plugin
  - [ ] Say text on specified intervals
- [ ] Weather elsewhere plugin - ability to retrieve weather for other city / station

Misc:

- [ ] Lint (flake8, black, mypy)
