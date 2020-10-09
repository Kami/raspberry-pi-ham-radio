# Raspberry Pi Ham Radio Controller

This repository contains source code and related information which allows users to expose various
information over ham radio frequencies.

## Notes

This setup assumes weather station can connect to a WiFi network which is needed for for operation.

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
- Document how to install text to spech and other dependencies

## Radio Setup

- We use VOX functionality so we don't need more hardware to trigger PTT, not 100% ideal, but
  works for this use case.

## Weather Station Setup

WIP

- Configure weather station to send data to local wx server.

## Software

This repository consists of 2 Python projects.

1. ``wx_server`` - this project consists of a HTTP server to which weather station can send data in
  Ecowitt format and this data is then formatted and persisted on disk. Data is persisted as serialized
  Protobuf messages in files per disk - one file per observation.

