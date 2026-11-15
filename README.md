# LavinOko forecast archive

Every mountain weather forecast [LavinOko](https://github.com/StamenchoBog/lavinoko) issued, stored exactly as
issued, twice a day from October to June and once a month in summer. It exists so the forecasts can be checked against what actually happened
on the mountain, and so the results can be published.

These are **weather forecast model values, not measurements and not avalanche danger ratings.**

## Files

```
weather/YYYY/MM/YYYY-MM-DDTHHZ.json.gz    one forecast run, UTC hour of issue
```

Each file is gzipped JSON (about 300 KB) with:

| Field | Content |
|---|---|
| `format` | Version of this layout (currently 1) |
| `issued_utc` | When the forecast was issued |
| `models` | Models used, and whether each was healthy in this run |
| `thresholds` | The alert thresholds in force at the time |
| `points[]` | One per forecast point: place, point id, position, elevation |
| `points[].hourly` | The blended forecast the website shows: 4 days back, 4 days ahead, hourly, local time (`Europe/Skopje`) |
| `points[].models_hourly` | Each model's own series (variables suffixed `_icon_eu`, `_gfs_seamless`, `_meteofrance_seamless`); `null` if that request failed |

Read one in Python:

```python
import gzip, json
run = json.loads(gzip.decompress(open("weather/2026/11/2026-11-15T06Z.json.gz", "rb").read()))
```

## How it is made

`.github/workflows/fetch.yml` runs on a schedule and calls the workflow in the LavinOko repository, which fetches
the forecast and commits the file here. Nothing else writes to this repository.

## Licence

- **Data** (`weather/`): weather data by [Open-Meteo.com](https://open-meteo.com) (CC BY 4.0), from the models of
  DWD (ICON-EU), NOAA (GFS) and Météo-France. Shared under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
  with that attribution. It was fetched under Open-Meteo's free non-commercial terms and is for non-commercial use.
- **Workflow file** (`.github/`): MIT, see `LICENSE`. The MIT licence does not cover the data.
