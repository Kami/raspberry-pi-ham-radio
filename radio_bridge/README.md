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
Rasbperry Pi GPIO pin.

Keep in mind that in the GPIO case, you need additional hardware component which will correctly
enable TX on your radio when voltage is present and disable it when voltage is removed.

The project itself took a lot of inspiration and ideas from other similar projects such as
[SVXLink](https://www.svxlink.org/), [Hambone](https://github.com/notpike/Hambone/) and
others.

Special thanks to the authors and contributors of those other projects.

<insert demo video link>

## Features

- Easy configuration via ``.ini`` style config file
- Various abuse prevention and other safe guards built in:
  - Ability to set maximum audio duration for all the audio files and text which is played on the
    frequency (to prevent potentially bad plugins or user actions from keeping the frequency open
    for too long).
  - Ability to set minimum run time for cron plugin jobs (to prevent potentially bad configuration
    or similar for running jobs too often).
  - Ability to set maximum transmission time. If plugin will run longer for a defined threshold,
    it will be automatically killed and TX will be disabled.
  - Minimum delay between DTMF commands invocations to prevent spam and abuse.
- Support for multiple text to speech engines (gtts - internet access needed, espeak ng - no internet
  access needed)
- Extensive caching for fast performance - synthesized audio files are cached so they can be
  re-used on subsequent plugin invocation if the text stays the same. This way we can avoid TTS
  step in many cases.
- Easy extensibility by writing custom Python plugins
- Ability to enable / disable specific plugins
- Support for admin plugins / commands which are protected using special OTP mechanism which is
  more secure than static code approach used by most other similar software
- Easy testing and development using built-in emulator mode where DTMF sequences are entered
  directly using a keyboard
- Support for converting text to morse code and playing it
- Support for playing morse code directly
- Audit logs - all the executed commands are logged under ``AUDIT`` log level

## Installation

You can install latest in development version using pip directly from git:

```bash
pip install "git+https://github.com/Kami/raspberry-pi-ham-radio.git@master#egg=radio_bridge&subdirectory=radio_bridge"
```

## Configuration

Radio bridge can be configured via ``.ini`` style configuration file.

Default configuration which describes available options and includes some examples can be found at
[conf/radio_bridge.example.conf](conf/radio_bridge.example.conf).

You can specify path to a configuration value to use by setting ``RADIO_BRIDGE_CONFIG_PATH``
environment variable as shown below.

```bash
RADIO_BRIDGE_CONFIG_PATH=/etc/radio_bridge/radio_bridge.conf radio-bridge
```

Starting it with ``--emulator`` and ``--dev`` flag which comes handy during testing and
development:

```bash
export RADIO_BRIDGE_CONFIG_PATH=/etc/radio_bridge/radio_bridge.conf
radio-bridge --emulator --dev --debug
```

In emulator mode, DTMF sequences can be entered via keyboard and dev mode means that some abuse
prevention checks won't be performed.

For production deployments, you are encouraged to user supervisord or a similar service manager.

You can find an example supervisord config at
[conf/radio_bridge.supervisord.example.conf](conf/radio_bridge.supervisord.example.conf)

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

### Regular Plugins

| Name | DTMF Sequence | Requires Internet Connection | Supported Languages | Description | Example Recording |
| --- | :---: | :---: | --- | --- | --- |
| Help | ``12`` | No | English | Display all the available DTMF commands. | [plugin_help.mp3](https://raw.githubusercontent.com/Kami/raspberry-pi-ham-radio/master/radio_bridge/examples/audio/plugin_help.mp3) |
| Clean DTMF Sequence | ``*D*`` | No | English | Special plugin which clears all the currently accumulated DTMF sequence. Comes handy in case of a typo and similar. | none |
| Current Time | ``21`` | No | English, Slovene | Say current local time for local timezone and UTC. | [plugin_current_time.mp3](https://raw.githubusercontent.com/Kami/raspberry-pi-ham-radio/master/radio_bridge/examples/audio/plugin_current_time.mp3) |
| Local Weather | ``34`` | No | English | Display weather information for a local weather station connected to this Raspberry Pi | [plugin_local_weather.mp3](https://raw.githubusercontent.com/Kami/raspberry-pi-ham-radio/master/radio_bridge/examples/audio/plugin_local_weather.mp3) |
| Location Weather | ``35??`` | Yes | English | Display weather for a specific location. Data is retrieved from vreme.arso.gov.si | [plugin_location_weather_ljubljana.mp3](https://raw.githubusercontent.com/Kami/raspberry-pi-ham-radio/master/radio_bridge/examples/audio/plugin_location_weather_ljubljana.mp3) |
| Repeater Info | ``38??`` | Yes | English | Display information for a specific VHF / UHF repeater. Data is retrieved from rpt.hamradio.si | [plugin_repeater_info.mp3](https://raw.githubusercontent.com/Kami/raspberry-pi-ham-radio/master/radio_bridge/examples/audio/plugin_repeater_info.mp3) |
| Traffic Information | ``25?`` | Yes | English, Slovene | ``251`` to display recent traffic information and events (incidents, road works) and ``252`` to display border crossings delays. |
| SPIN Events | ``26`` | Yes | Slovene | Retrieve information about most recent interventions and accidents. |
| Cron Say | none | No | English | Plugin which allows various announcements and information defined in the config to be played at defined intervals. | none |
| Record Audio | none | none | none | Plugin which records audio from the audio in and stores it in a file. This can be useful when troubleshooting things, etc. | none |

NOTE: Sequences in the table above are default sequences defined in the code base. Those can be
overwritten / changed on per plugin basis inside the config.

#### Cron Say Plugin

Currently the following values are available in the context which is used when rendering the text
value:

* ``day_of_week`` - Current day of the week.
* ``date`` - Current date in YYYY-MM-DD format
* ``time_utc`` - Current time in HH:MM format (UTC)
* ``time_local`` - Current time in HH:MM (local timezone)
* ``weather_data`` - Weather observation for local weather station (if any observation is
   available).
* ``callsign`` - Value of the ``tx.callsign`` configuration option.

### Admin Plugins

| Name | DTMF Sequence | Requires Internet Connection | Description |
| --- | :---: | :---: | --- |
| Change TTS Mode | ``92xxxx?`` | No | Change TTS mode to online (gtts) / offline (espeak). For example 92xxxx1 for online and 92xxxx2 for offline. |
| Disable non-admin DTMF commands | 93xxxx | No | Disable all the non-admin DTMF commands. |
| Enable non-admin DTMF commands | 93xxxx| No | Enable all the non-admin DTMF commands (if they have been previously disabled via admin command). |

In all the admin plugins ``xxxx`` should be replaced with actual valid and unused OTP pin code. For
example, if plugin DTMF sequence is ``92``, ``data`` value is ``1`` and OTP value is ``9876``, you
would enter the following DTMF code to active this plugin: ``9298761``.

Plugins which modify configuration state (enable DTMF commands, disable DTMF commands, etc.) update
config file which is specified as part of ``RADIO_BRIDGE_CONFIG_PATH`` environment variable on disk.

## Note on Timezone

Te software has been designed to work with UTC. This means you are strongly encouraged to set
timezone on your server / Raspberry Pi to UTC to avoid timezone related issues.

Only exception to that is "current time" plugin which plays both, the local and UTC time. To
be able to play local time correctly, you need to set ``plugin:current_time.local_time``
configuration option so it matches your local timezone (e.g. ``Europe/Ljubljana``).

## Note On DTMF Admin Commands and Security

For convenience, this software currently exposes a couple of admin DTMF commands with limited
functionality - one for disabling all the DTMF triggered plugins (minutes the admin commands)
and one for re-enabling them.

The primary goal of the implementation and those commands is ease of use. This means we should
only require the operator to enter a short DTMF sequence to activate those admin commands /
plugins.

This of course represents a challenge since we can't perform any kind of more complicated
encryption and key exchange scheme over an insecure channel (radio waves).

Any kind of more complex scheme would require more interaction, potentially a dedicated
Android application (or similar) which performs the key exchange and encryption using DTMF
tons and / or possible also an internet connection (on both sides - e.g. challenge response + OTP
mechanism, time limited OTP code over SMS or similar).

In addition to that, using encryption on ham bands is forbidden in most countries.

On the other hand, we can't use static codes either (a lot of other echolink based software does
that), since they offer almost no protection and can easily be sniffed and replayed by other
listeners on the frequency.

As a slightly more secure alternative, this software implements an approach where the server
generates a small set of unique and randomly generated single use codes for each admin command
on server startup.

Those codes can then be saved locally by the operator and used to execute admin commands. To
prevent replay attacks, each code is only valid for single use.

Keep in mind that this approach is not a proper encryption and security mechanism and should not be
treated as such - it has many possible attack vectors and weaknesses (brute force attacks, etc.).

That's also the reason why only non-destructive functionality is exposed via admin commands.

## Note on Power Consumption

The software was primarily tested on Raspberry Pi 4 model b. To measure power consumption, I used
of the shelf power meter.

Power consumption in idle modle (without this software running) was ``2.5 W`` and power
consumption with this software running in the idle "DTMF decoding" loop was between
``3.0`` - ``3.5`` W.

Currently the most CPU intensive part is DTMF decoding algorithm which pretty much runs all the
time during the life time of this program (this is needed to be able to detect and decode any
transmitted DTMF sequences).

In the future, there is a plan to implement a low power / sleep mode. In that mode, user will be able
to either completely turn DTMF decoding off or enable special "sleep mode" where the software will
only for DTMF codes on a specific interval (e.g. every 10 past the whole hour or every 10 minutes
for 1 minute) and if any DTMF code will be detected during that time interval, software will go
fully running / awake mode for a specific duration (configurable via config).

Primary situation where low power / sleep mode comes handy is when deploying this software on a
RPi which is powered by external battery (e.g. power bank) and connected to battery powered hand held
radio.

Such deployment may come handy in various emergency situations.

Based on initial testing, estimated RPi power consumption in in lower power / sleep mode will be
around ``2.5`` - ``3.0`` W.

As an alternative, you should also be able to run this software on RPi which has lower power
consumption out of the box, but this hasn't been tested yet.

## Note on VOX Transmission Mode

When using VOX mode and VOX functionality of your radio it's important you set audio out levels on
the Raspberry PI correctly to they will indeed trigger a TX when audio file is being played.

Actual audio out volume level you need to set very much depends on your USB sound card and your
radio.

I was testing it with ``Baofeng GT-3TP III`` and ``Sabrent USB External Stereo Sound Adapter`` USB
sound card and I needed to set audio out vole to around ``60%``.

You can set audio volume levels for the USB sound card output and input using ``alsamixer``.

## Note on plugin DTMF codes

When defining custom DTMF trigger codes for the plugins or developing custom plugins, you should
follow those rules:

* Make sure that plugins use the same number of DTMF characters (e.g. 2)
* Make sure that you never use the same character multiple times. For example ``12`` is OK, but
  ``11`` is not. The reason for that is that most of the DTMF detection / decoding algorithms don't
  allow repeated sequences to increase decoding accuracy (aka it's hard to distinguish if user 
  entered the same DTMF code twice or it simply help the key for a longer period or similar).

Example of good DTMF sequences:

* ``12``
* ``13``
* ``23``
* ``34??``
* ``35??``

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
```

## Usage

### Recording custom hello and callsign message using gtts-cli

Before playing each audio file / message, this software will always first play the callsign.

Callsign can be configured via ``tx.callsign`` configuration option. This can either contain an
actual  callsign which will be synthesized to audio and played or a path to an .mp3 / .wav file
which will be played.

Example below shows how to record a custom call sign / hello message using ``gtts-cli`` tool.


```bash
gtts-cli -l en-us --slow --nocheck "SIERRA FIVE TWO TANGO ECHO SIERRA TANGO" > /tmp/audio_files/callsign.mp3
```

## TODO

Main

- [ ] Multi language support
- [ ] Permanent / scheduled "low power" / "sleep mode" mode
  - [ ] Ability to turn off DTMF decoding and DTMF plugins in the config - in that scenario, only
        cron plugin will run. This may come handy in various scenarios where you only want to run
        cron plugin which periodically transmits an announcement or similar
  - [ ] Ability to on "sleep mode" which will cause the software to only listen for commands during
        specific time frames (e.g. for 1 minute past 10 minute mark) and if any command is detected
        during that window, software will go out of sleep mode for the pre-defined amount of time.
Misc:

- [ ] Support expiring dict plugin local cache when using process plugin executor.

DTMF Decoding

- ~~[ ] Implement Goertzel algorithm based DTMF decoding~~ - Based on the research and micro
   benchmarking, current FFT based algorithm which utilizes numpy is more efficient than
   alternative implementations.

Plugins

- [ ] Support Jinja templates for cron plugin text strings.
- [ ] Simplex repeater mode

CI/CD

- [ ] Automatic deployment of new version of this software to RPI devices which are connected to
      the internet on merge / push to master.
