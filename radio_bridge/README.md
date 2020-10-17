# Raspberry Pi Ham Radio Bridge

This project implements ham radio automation platform which is meant to be deployed on a Raspberry
Pi or a similar Linux based device.

It allows ham radio operators to expose various functionality via DTMF codes (current weather
information, etc.) and perform other automated operations (e.g. automatically play announcement
messages on a pre defined time interval).

The project is meant to be connected to a radio or a repeater via small USB sound card dongle which
is plugged into Raspberry Pi.

It supports two transmit (TX) mode - first one relies called ``vox`` relies on VOX functionality of
a radio and the second one called ``gpio`` triggers a TX by opening (supplying voltage) on a specific
Rasperry Pi GPIO pin.

Keep in mind that in the GPIO case, you need additional hardware component which will correctly
enable TX on your radio when voltage is present and disable it when voltage is removed.

## Features

- Easy configuration via ``.ini`` style config file
- Various abuse prevention and other safe guard built in
- Support for multiple text to speech configuration (gtts - internet access needed, espeak ng - no internet
  access needed)
- Easy extensibility by writing custom Python plugins
- Easy testing and development using built-in emulator mode where DTMF sequences are entered
  directly using a keyboard
- Support for converting text to morse code and playing it
- Support for playing morse code directly
- Audit logs - all the executed commands are logged under ``AUDIT`` log level

## Plugins

This project supports 3 type of plugins.

### 1. Non-DTMF plugins

Those plugins are activated by some other mechanism and not via DTMF code. An example of such
plugin is ``cron`` plugin which allows operator to schedule text / audio file to be played at
defined intervals (e.g. every hour, once a day, every Monday, etc).

### 2. Fixed code DTMF plugins

Those plugins are activated by a fixed DTMF code. An example of such plugin is ``current_time``
``help`` and ``local_weather`` plugin.

### 3. Dynamic code DTMF plugins

Those plugins are activated by a fixed DTMF code, but also take additional dynamic DTMF sequence
after the plugin DTMF sequence code. This dynamic part of the code is then passed to the plugin
``run()`` method.

An example of such plugin is ``location_weather`` plugin which allows user to retrieve weather
for different pre-defined locations.

### Available Plugins

## Development

TBW.

```bash
PYTHONPATH=wx_server:radio_bridge:. python radio_bridge/radio_bridge/main.py
```

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
- [ ] Ability to enable and disable TX via GPIO pin when VOX mode is not used
- [ ] Max TX time safe guard - if TX has been on more than X seconds, disable it.
- [ ] Rate limiting / abuse prevention - each command can run x times per time period, depending
  on the command / plugin
- [ ] Move common logging, config parsing code into common pacakge
- [ ] Ability to enable specific plugins
