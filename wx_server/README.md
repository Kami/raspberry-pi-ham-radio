# Weather Station Observations Server

This project consists of an HTTP server which accepts weather observations in Ecowitt format over
HTTP and stores it to a file on disk.

Weather observation data is processed, normalized, serialized to Protobuf and written to a file on
disk.

Currently it supports 1 minute reporting interval. Each observation is stored in a specially
formatted and named file on disk which can be retrieved later on.

By default, observations are stored in the following directory
``/opt/data/<station id>/<YYYY>/<MM>/<DD>`` and the file name is in the following format
``observation_<hh><mm>.pb``

Server supports receiving and persisting observations from multiple data stations (data for each
station is persisted in a separate directory).

Weather stations should send observations using HTTP POST method to the following URL:

1. For data in Ecowitt format: ``http(s)://<listen ip>:<listen port>/v1/wx/observation/ew/<station id>/<station secret>``.
2. For data in WeatherUnderground format: ``http(s)://<listen ip>:<listen port>/v1/wx/observation/wu/``

## Configuration

### Server

Example configuration can be found at ``wx_server/conf/wx_server.conf``,

To add a new station, add en entry to ``[secrets]`` section in the configuration file. Key name
is station id (e.g. ``home``) and the value is SHA256 hash of ``<station id>:<station secret>``.

For example, if the station id is ``home`` and the secret is ``foobar``, you can obtain SHA 256
hash of this value by running the command shown below:

```bash
python3 -c 'import hashlib ; print(hashlib.sha256(b"home" + b":" + b"foobar").hexdigest())'
```

### Weather Station

Actual weather station configuration very much depends on the weather station model you have.

The screenshot below shows how you can configure ``Sainlogic Professional WiFi Weather Station``
via the Android application.

Ecowitt format:

![Screenshot_20201024_133655_com ost wsview](https://user-images.githubusercontent.com/125088/97113784-da919900-16ec-11eb-9735-132f8bb29b38.jpg)

WeatherUnderground format:

![Screenshot_20201024_133613_com ost wsview](https://user-images.githubusercontent.com/125088/97113789-e3826a80-16ec-11eb-9c56-a5b3d91ed1a4.jpg)

In this screenshots, ``192.168.160.247`` is the IP address of Raspberry PI, ``home`` is the weather
station name and ``foobar`` is the password / secret.

## Running The Service

You can run the service using ``wx_server/bin/wx-server`` script as shown below:

```bash
WX_SERVER_CONFIG_PATH=/etc/wx_server/wx_server.conf ./wx_server/bin/wx_server
```

For production deployments, you are encouraged to user supervisord or a similar service manager.

You can find an example supervisord config at
[conf/wx_server.supervisord.example.conf](conf/wx_server.supervisord.example.conf)

## Development

### Running the WSGI Server

```bash
PYTHONPATH=../:.: gunicorn --bind 0.0.0.0:8000 --worker-class gevent --workers 1 --threads 8 wx_server.wsgi:app
```

## Cleanup

## Deleting Old Observation

On average, each file with observation data should be around 70 bytes in size which means
that a year worth of data with 1 minute resolution will take around 35 MB space on disk
(24 * 60 * 360 * 70).

If you want to automatically delete old observations, you can do that using a simple cron job as
shown below.

NOTE - If we didn't care about decimal precision and we stored most values as ints instead of
floats, we could, on average, reduce file size by at least 50%.

Keep in mind that Protobuf format is already efficient, especially for numbers, so compression
won't get you anything in this case - in fact, the compressed file size will be larger than the
original.

```bash
# Delete files older than 300 days
find <data dir> -name "*observation*.pb" -mtime +300 -print0 | xargs -0 rm
```
