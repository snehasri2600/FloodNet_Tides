# tidal_analysis pipeline

Builds a unified NOAA + USGS tidal dataset (astronomical height + storm surge, all 6
NYC-area stations) and uses it to test whether each FloodNet sensor's flood timing
clusters around high tide (Rayleigh test on lag-to-high-tide).

## Run order

1. **`1_tidal_data_format_conversion.ipynb`** — fetches NOAA predicted tides and USGS
   observed water levels (2025–2026), applies UTide harmonic analysis to extract
   clean high/low extrema from the noisy USGS series, converts both sources to a
   common NAVD88 datum, and combines them into one schema.
   - writes: `tide_predictions.geojson`, `usgs_water_levels.geojson` (intermediate,
     gitignored), `tidal_unified.geojson` (the shared output, gitignored)
2. **`2_tidal_analysis.ipynb`** — reads `tidal_unified.geojson` and
   `../final_deployed_sensors.geojson`, joins each flood event to its nearest tidal
   station, computes signed lag to the nearest high tide, and runs a Rayleigh test
   per sensor to classify tidal vs. non-tidal flooding.
   - writes: `silent_sensors_report.csv`, `silent_sensors_year_breakdown.csv`,
     `silent_sensors_gap_tiers.csv` (an earlier, sensor-subset version of the
     network-wide gap analysis later redone in `3_data_gap_exploration/1_gap_tiers/`)

## Reruns

Neither notebook caches its NOAA/USGS fetch by default — `1_tidal_data_format_conversion.ipynb`
checks for its output `.geojson` files on disk and skips the fetch if they already
exist (set `FORCE_REFRESH = True` to force a fresh pull). `2_tidal_analysis.ipynb` always
fetches flood events live from NYC Open Data.
