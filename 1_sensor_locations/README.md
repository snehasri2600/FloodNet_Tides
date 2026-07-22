# sensor_locations pipeline

Builds the repo's shared master sensor table (`../final_deployed_sensors.csv` /
`.geojson`) by merging NYC Open Data's FloodNet metadata with Directus's active-device
records, then flags coastal/floodplain sensors and diagnoses labeling mismatches
between the two systems.

## Run order

Run order here is a hard dependency, not just convention — later notebooks pull
variables from earlier ones via Jupyter's `%store` magic, so skipping ahead will fail.

1. **`1_Directus_Data.ipynb`** — reads `deployed_sensors_directus.json`, filters to
   coastal sensors, and `%store`s `coastal_sensors` for the next notebook.
2. **`2_FloodNet_Sensor_Locations.ipynb`** — the main build. Fetches NYC Open Data's
   FloodNet metadata + floodplain boundaries, merges in Directus data (`%store -r
   coastal_sensors`), reconciles name mismatches (whitespace/case differences and
   retired-sensor drops), and writes `../final_deployed_sensors.csv` /
   `.geojson`. Also `%store`s `NaN_deploy_type_sensors` for the next notebook.
3. **`3_NaN_sensor_comaprisons.ipynb`** — reads `directus_all_deployments.csv` and
   `%store -r NaN_deploy_type_sensors` for a deeper look at sensors with unresolved
   `deploy_type` labels.

## Reruns

No caching here — every notebook always re-fetches live from NYC Open Data / Directus.
Rerunning in order is cheap (small datasets) but does hit both APIs each time.
