# Raspberry Pi Ham Radio Controller

[![CI](https://github.com/Kami/raspberry-pi-ham-radio/workflows/CI/badge.svg?branch=master)](https://github.com/Kami/raspberry-pi-ham-radio/actions)

This repository contains source code and related information which allows users to expose various
information on a ham frequency and perform various DTMF code and other related automations using
Raspberry Pi or a similar low powered device.

It was primarily designed to be deployed next to and connected directly to a VHF / UHF repeater.

It consists of two sub-projects:

1. [Weather Observation Server](wx_server/) - HTTP server which receives weather observations from a local
  Weather station and persists them on disk.
2. [Radio Bridge Server](radio_bridge/) - Software which exposes various functionality on a ham
  radio frequency.

**NOTE: This project is work in progress and under development. Do not use it for anything critical.**

## Supported Python versions

* Python 3.6
* Python 3.7
* Python 3.8
* Python 3.9

## Notes

This setup assumes weather station can connect to a WiFi network which is needed for the operation.

If there is no WiFi network available where you want to deploy this setup, you can configure
Rasperry Pi to acts as an Access Point to which Weather Station can connect.

This setup doesn't require internet connection, but it means weather station won't be able to
automatically synchronize time over the internet and you will need to configure it manually.

## Equipment / Requirements

* Baofeng GT-3TP or a similar radio with 2 pin connector
* Raspberry Pi (model 4b is recommended) and related accessories (micro sd card, good charger / power supply, fan is also recommended)
* USB sound card (e.g. https://www.amazon.de/-/en/gp/product/B00IRVQ0F8/ref=ox_sc_act_title_1?smid=A1S41JW81H0D20&psc=1) - needed so you can connect Radio to Raspberry Pi
* 3.5 male to 3.5 male cable, 3 part aka 2 black rings - to connect radio in to line out in USB sound card
* 2.5 male to 3.5 male, 3 part aka 2 black rings - to connect radio out to line in on USB sound card
* WS2900 Weather Station (http://www.foshk.com/Wifi_Weather_Station/WH2900.html)

## Configuring Raspberry Pi

TBW.

- Document how to configure USB sound card
- Document how to install text to speech and other dependencies
