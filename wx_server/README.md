# Weather Observations Server

## Development

### Running WSGI server

```bash
PYTHONPATH=../:.: gunicorn --bind 0.0.0.0:8000 --worker-class gevent --workers 1 --threads 8 wx_server.wsgi:app
```

## Deleting Old Observation

On average, each file with observation data should be around 70 bytes which means that a year worth
of data with 1 minute resolution will take around 35 MB space on disk (24 * 60 * 360 * 70).

If you want to automatically delete old observations, you can do that using a simple cron job as
shown below.

NOTE - if we didn't care about decimal resolution and we stored most values as ints instead of
floats, we could, on average, reduce file size by at least 50%.

Keep in mind that Protobuf format is already efficient, especially for numbers, so compression
won't get you anything in this case - in fact, the compressed file size will be larger than the
original.

```bash
# Delete files older than 100 days
find <data dir> -name "*observation*.pb" -mtime +100 -print0 | xargs -0 rm
```

## Example Request Data (ecowitt format)

```python
{'PASSKEY': '42B056FC063605F951D8D3BAA00037C1', 'stationtype': 'EasyWeatherV1.5.4', 'dateutc': '2020-10-03 16:22:18', 'tempinf': '72.7', 'humidityin': '72', 'baromrelin': '29.481', 'baromabsin': '28.701', 'tempf': '61.3', 'humidity': '99', 'winddir': '264', 'windspeedmph': '2.5', 'windgustmph': '3.4', 'maxdailygust': '3.4', 'rainratein': '0.472', 'eventrainin': '1.701', 'hourlyrainin': '0.220', 'dailyrainin': '1.701', 'weeklyrainin': '2.559', 'monthlyrainin': '1.720', 'totalrainin': '4.350', 'solarradiation': '3.79', 'uv': '0', 'wh65batt': '0', 'freq': '868M', 'model': 'WS2900_V2.01.10'}
```
