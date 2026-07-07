---
name: new-date-changes
description: Exact changes needed across notebooks to extend data coverage back to 2025
metadata:
  type: project
---

Changes needed to add data starting in 2025 (currently everything starts 2026-01-01).

## `tidal_data_format_conversion.ipynb`

**Cell 0 — NOAA year constant:**
```python
YEAR = 2026  # → fetch 2025 too
```
`fetch_predictions()` fetches month-by-month for a single year. Either change to `YEAR = 2025` or loop over `[2025, 2026]` and concatenate.

**Cell 4 — USGS start date:**
```python
START_DT = "2026-01-01"  # → "2025-01-01"
```
`END_DT` is already dynamic (`pd.Timestamp.today()`), so only the start needs updating.

**Output filenames** — rename or drop the year suffix on:
- `tide_predictions_2026.geojson`
- `usgs_water_levels.geojson`
- `tidal_unified_2026.geojson`

## `tidal_analysis.ipynb`

**Cell 6 — flood events Socrata query:**
```python
WHERE flood_start_time > "2026-01-01T11:42:38"
# → "2025-01-01T00:00:00"
```

**Cell 11 — tidal data input file:**
```python
tidal_unified_2026 = gpd.read_file('tidal_unified_2026.geojson')
# → update filename to match whatever the conversion notebook outputs
```

## Not affected
- `final_deployed_sensors.geojson` — sensor metadata, not time-series
- Floodplain boundaries (`ek8y-fsqz`) — fetched live from Socrata, not date-gated
- `FloodNet_Sensor_Locations.ipynb` / `Directus_Data.ipynb` — no date filtering

## Notes
- USGS `get_iv` pulling 2 years of 15-min data (4 stations) is a larger fetch — slower but should work.
- After changes, re-run `tidal_data_format_conversion.ipynb` first to regenerate the unified geojson, then re-run `tidal_analysis.ipynb`.
