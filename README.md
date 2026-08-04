# FloodNet Tides

Project analyzing [FloodNet](https://www.floodnet.nyc/) — NYC's street-level flood
sensor network. Two goals:

1. **Correctly classify which FloodNet sensors are tidally influenced**, by joining real
   NOAA/USGS tidal data to sensor flood-event timing (a Rayleigh test on lag-to-high-tide),
   rather than relying on the network's existing manual `tidally_influenced` label.
2. **Document a real data-quality problem** found along the way: a large share of FloodNet's
   public NYC Open Data feed shows zero flood events for sensors that were deployed and live
   all of 2025 — investigated, verified, and corroborated independently (see
   [Key findings](#key-findings)) for eventual report-back to FloodNet/DEP.

## Pipeline

Three stages, run in order — each folder has its own README with exact notebook-level
run order and file dependencies:

| # | Folder | What it does |
|---|---|---|
| 1 | [`1_sensor_locations/`](1_sensor_locations/README.md) | Merges NYC Open Data's FloodNet sensor metadata with Directus's active-device records, reconciles naming mismatches between the two systems, and builds the repo's shared master sensor table. |
| 2 | [`2_tidal_analysis/`](2_tidal_analysis/README.md) | Builds a unified NOAA + USGS tidal dataset (astronomical height + storm surge, harmonic-analysis-cleaned) and tests whether each sensor's flood timing clusters around high tide. |
| 3 | [`3_data_gap_exploration/`](3_data_gap_exploration/README.md) | Sizes the 2025 data gap network-wide, then corroborates a hand-logged sample of missing events against rain, tide/surge, and nearby 311 calls to confirm they're real floods, not noise. |

`final_deployed_sensors.csv` / `.geojson` (repo root) are the shared output of stage 1 —
every downstream notebook across stages 2 and 3 reads them from here.

## Setup

**Python packages:** `pandas`, `geopandas`, `shapely`, `numpy`, `scipy`, `requests`,
`folium`, `branca`, `utide`, `dataretrieval`, `scikit-learn`.

**NCEI CDO API token** (for `3_data_gap_exploration/2_weather/Weather_Data_Scrape.ipynb`):
get a free token at https://www.ncei.noaa.gov/cdo-web/token, then copy
`3_data_gap_exploration/2_weather/.ncei_token.example` to `.ncei_token` in that same folder
and paste the token in as the only line. `.ncei_token` is gitignored; never commit a real
token.

## Reproducibility

Several data files are gitignored because they're large (some would exceed GitHub's 100MB
limit) and are fully reproducible by re-running the notebook that built them:

- `2_tidal_analysis/tidal_unified.geojson`, `usgs_water_levels.geojson`,
  `tide_predictions.geojson` — regenerate via `1_tidal_data_format_conversion.ipynb`.
- `3_data_gap_exploration/3_tidal/noaa_observed_water_levels.csv` — regenerate via
  `Tidal_Corroboration.ipynb`.
- `3_data_gap_exploration/4_311/flooding_311_2025.csv` — regenerate via
  `311_Call_Verification.ipynb`.

All three are cached with a `FORCE_REFRESH` flag in their respective notebooks, so a normal
rerun after the first fetch is fast and hits no external API.

## Key findings

- **The 2025 data gap is real and network-wide.** 111 of 415 deployed sensors (27%) had real
  exposure time in 2025 — a full year or partial window — and logged zero flood events in
  FloodNet's public feed, despite the network overall logging more events (678) and more
  distinct reporting sensors (151) that year than any prior complete year. Ruled out: API
  row-limit truncation (every fetch verified against an independent `count(*)`), sensor
  retirement, and hardware failure (broken-status rate is actually *lower* in the silent
  group than the rest of the network).
- **The gap isn't limited to tidal/coastal sensors.** An earlier pass restricted to the
  ~200-sensor tidal/floodplain candidate set found 74 silent sensors; the full 415-sensor
  network run roughly doubled that.
- **A hand-logged sample of missing events is independently corroborated, not noise.** Of
  227 manually-logged missing-flood events (11 sensors), 100 (44%) have at least one
  independent corroborating signal — rain, an unusually high/surging tide, or a nearby
  same-day 311 call. Sensors without a signal mostly reflect that rain doesn't apply to
  coastal sensors (and vice versa for tide/surge), not an absence of evidence.
- **Day-level tide/surge testing doesn't show extreme-tide flooding driving the no-rain
  events** — but this is consistent with *ordinary* tidal flooding (which scores near the
  null on a day-level test), not evidence against it. Distinguishing the two needs sub-daily
  flood timestamps and the phase-based Rayleigh test in `2_tidal_analysis.ipynb`.

See `3_data_gap_exploration/README.md` and `2_tidal_analysis/README.md` for the full
methodology behind each of these.
