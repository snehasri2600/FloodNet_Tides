**Sensor Placement Investigation — Methodology**

**Purpose**  
Find FloodNet sensors that are missing floods they should be catching, and figure out whether that's because the sensor is misplaced or because the sensor is just sitting somewhere that doesn't flood. Output is a ranked list of relocation candidates for the team to physically check — not a final verdict.

**Background**  
FloodNet's public feed has a confirmed 2025 data gap: 111 of 415 sensors show zero events for part or all of 2025, verified against the feed's own count(\*), not just corroboration. That gap is a reporting problem, not a placement problem, and it has to be separated out before any placement conclusion is drawn — a gap-affected sensor looks silent no matter where it's installed.

**Hypothesis**  
A sensor that misses floods on days when flooding was plausible and on days when nearby evidence says flooding actually happened locally is a placement candidate. A sensor that misses floods only when the evidence for local flooding is weak is probably just sitting in a low-flood-risk spot, not misplaced.

**Sensor Groups**

* **Gap-tier sensors** — already known to have zero/partial 2025 feed coverage, per floodnet\_full\_network\_gap\_tiers.csv (lists sensors in gap Tiers 1-4, 175 rows). Any sensor not in that file is assumed non-gap-tier (clean). Excluded from ranking, reported separately, flagged "feed-gap affected — placement undetermined."  
* **Non-gap-tier sensors** — everything else. These get ranked.

**Analysis Window**  
All exposure and flood-plausible-day calculations run through **2026-07-02** — the latest date currently available in tidal\_unified.geojson, used here as the network-wide cutoff. All source APIs (NCEI, NOAA/USGS, Socrata 311) update at least daily, so reaching this date is a re-pull, not new data acquisition — but the three existing datasets aren't in the same state:

* **noaa\_observed\_water\_levels.csv** and **flooding\_311\_2025.csv** are genuinely continuous (366 and 365 straight days of 2025 respectively) — just need their date range extended to 2026-07-02.  
* **nyc\_precipitation\_by\_date.csv** is NOT continuous — despite the name, it only has 128 unique dates, exactly matching the 128 hand-logged QC dates. Getting continuous daily rain data means writing new fetch logic (loop over every day in range), not just extending a date range on an existing pull.

**Core Metric: Miss Rate**  
miss rate \= (flood-plausible days with zero logged events) / (flood-plausible days since install)

A day is flood-plausible if at least one applies: rain, elevated tide/surge, a nearby sensor detection, or a nearby 311 flooding call. Matching for nearby-sensor and 311 signals uses a **±1 day lag window**, same as the existing tidal lag model — floods don't always register same-day.

**Local Flood Risk — Three Separate Tests**  
Rain and tide/surge are city/region-wide, so they can't tell a misplaced sensor apart from a sensor correctly sitting in a dry spot. Local flood risk fixes that, tested three ways:

* **Test A — 311-based:** hyperlocal 311 flooding complaints near the sensor (tight radius, not the citywide 311 signal used in the miss-rate calc).   
  * 311 complaint counts are normalized against that area's overall 311 call volume (any complaint type, same period) — a cheap partial control for reporting bias, since an area with lots of 311 activity generally but zero flooding complaints is different from an area with almost no 311 activity at all. Doesn't fully fix the bias — a resident-engagement gap can still mask real flooding — but it's the only affordable control available, and gets flagged as a caveat regardless.  
* **Test B — nearby-sensor-based:** does each sensor's single nearest neighbor (k=1, capped at 3,500 ft — see Step 2) also detect flooding nearby? A fixed radius didn't work (see Step 2); k=1 with this cap is the actual method. Sensors with no neighbor inside the cap get flagged "no comparable neighbor" and excluded from Test B specifically.  
  * Any neighbor's detection (gap-tier or not) counts as positive evidence.  
  * Only a non-gap-tier neighbor's silence counts as negative evidence.  
  * "No comparable neighbor" flag is based on whether the nearest neighbor is within the 3,500 ft cap, not a count within a radius. Note the 2nd-nearest sensor (also captured in `neighbors_df`) can't rescue a sensor whose 1st-nearest is already beyond the cap — it's always at least as far. It exists for a different case: **open question, not yet decided:** when the 1st-nearest sensor is gap-tier and silent (untrustworthy for negative evidence), whether to fall back to the 2nd-nearest sensor instead of treating it the same as "no comparable neighbor."  
* **Test C — combined:** local flood risk \= 311 signal OR nearby-sensor signal. For sensors with no neighbor (flagged in Test B), Test C falls back to 311 alone, and that sensor's combined score gets marked as single-signal / lower confidence rather than treated the same as a sensor with both.

**Small-Sample Correction**  
Applies everywhere — miss rate, Test A, Test B, Test C. A sensor with only 1-2 flood-plausible opportunities (new install, or few nearby comparisons) doesn't get a confident raw ratio; it gets pulled toward the network-average rate for that metric instead.

**Elevation**  
Not in final\_deployed\_sensors.geojson today — no elevation field exists there. Pulled separately via the USGS Elevation Point Query Service (free, no key, same "official government API" pattern as the NOAA/USGS tidal data already used in this project). Looked up inside 4\_sensor\_activity/, not written back into final\_deployed\_sensors.csv/.geojson — that file is read by 6 other notebooks across the repo, and this doesn't need to touch it.

**Combining Everything**  
**Not using a trained ML classifier —** there's no labeled set of known-misplaced sensors to train against (see Open Items below), so a random forest or similar would have nothing real to learn from and would be harder to explain to the team anyway. Instead: a **Poisson/binomial regression modeling expected detections as a function of rain, tide/surge, and elevation**, with sensor exposure time as an offset. Rank sensors by the residual — how far actual detections fall below what the model expected. This gets data-driven weights instead of hand-picked ones, folds elevation in naturally, and stays interpretable enough to hand to the team as real coefficients.

**Non-Gap Tier Sensor Results**

* **Ranked list of non-gap-tier sensors** by adjusted miss rate / regression residual — the relocation-candidate list.  
* Test A/B/C results reported alongside the ranking so disagreement between signals (e.g. high 311 risk but low neighbor-sensor risk) is visible, not hidden inside one combined number.

**Gap-Tier Sensor Results (Informational, Not Ranked)**  
Run the same methodology on the 111 gap-tier sensors, but treat the two halves differently:

* **Local flood risk (Tests A, B, C) doesn't depend on a sensor's own feed data** — it's computed the same way and is fully valid for gap-tier sensors. Report it normally; it's useful now (which gap-affected areas are actually flood-prone) and will matter more once the feed issue is resolved.  
* **Miss rate for gap-tier sensors is expected to read near 100%** because of the known feed gap itself, not placement. Report it for completeness, but flag it clearly as not usable evidence of misplacement.  
* **Keep gap-tier results in a separate table** from the main ranked list — don't interleave them, so the two aren't mistaken for comparable numbers.

**Open Items — Deferred, Not Blocking**

* **Catch basin/sewer infrastructure data** is available on NYC Open Data but needs separate download, parsing, and cleaning. Doable, but it's extra time and effort — pushed to a later date rather than this week's scope. Elevation is the stand-in for drainage effects until then, and doesn't capture actual pipe capacity or blockages.  
* **No sanity check / known-misplaced sensor exists** right now to validate the method against. That validation is on the team to do later, once the ranked list exists.

**Limitations**

* Every "flood-plausible" and "local flood risk" signal is a proxy, not confirmed ground truth.  
* 311-based local risk is biased by how often residents in an area report anything at all — **partially controlled for, not eliminated**.  
* A high miss rate suggests misplacement; it doesn't prove it. Someone still has to go check.  
* **Install-date accuracy for redeployed sensors is unverified.** Retired sensors were removed when final\_deployed\_sensors.csv/geojson was built, and the 415 current Directus sensors should be accurate and up to date — but if a sensor was replaced at the same location, date\_installed may reflect the original device rather than the current one, which would bias its exposure window. Not corrected in this pass; flagged for a future revisit if it turns out to matter.

---

**Step-by-Step Coding Methodology**

1. **Elevation lookup (USGS Elevation Point Query Service).**  
   1. Fully self-contained — just lat/long in, elevation out, scoped inside 4\_sensor\_activity/. No dependency on anything else, so it's a fast, isolated win to get out of the way early.  
   2. → verify: spot-check a couple of known NYC locations against expected elevation ranges.  
2. **Distance matrix between all sensors (from existing lat/long).**  
   1. A fixed radius doesn't work here — the network is too unevenly spread. At 500/1000/1500/2000 ft, 377/283/206/152 of 415 sensors had zero neighbors. Checked the actual nearest-neighbor distance distribution instead: median 1st-nearest is 1,487 ft, 90th pct 3,470 ft; going to k=3 or k=5 pushes the 90th pct out to 5,857 ft / 7,743 ft, which starts to blur back into the same city-wide scale rain/tide already cover. Settled on **k=1 (single nearest sensor), capped at 3,500 ft** (~90th pct of nearest-neighbor distance) — past that cap, "nearest" doesn't mean meaningfully local anymore, so those sensors are flagged "no comparable neighbor" rather than matched to a distant one.  
   2. → verify: check how many sensors have a neighbor within the 3,500 ft cap; the rest are genuinely isolated in this network, not a method failure.  
3. **Re-pull/extend rain, tide, and 311 datasets through 2026-07-02.**  
   1. Doesn't depend on anything above — same "no dependency, do it early" reasoning as elevation and the distance matrix. Extend noaa\_observed\_water\_levels.csv and flooding\_311\_2025.csv's date range; rewrite the precipitation pull to fetch continuously (every day in range) instead of only the 128 QC dates.  
   2. → verify: all three datasets have no gaps in daily coverage from their start date through 2026-07-02.  
4. **Split sensors into gap-tier vs. non-gap-tier.**  
   1. Reuses floodnet\_full\_network\_gap\_tiers.csv (3\_data\_gap\_exploration/1\_gap\_tiers/) — it lists only sensors with a Tier 1-4 gap in 2025 (175 rows). Any sensor not in this file is treated as non-gap-tier (clean) by default — join back against the full 415-sensor list rather than assuming this file alone is complete.  
   2. → verify: gap-tier count matches the 175 rows in floodnet\_full\_network\_gap\_tiers.csv; non-gap-tier count is 415 minus that.  
5. **Assemble flood-plausible-day signals per sensor (rain, tide/surge, nearby-sensor detection, 311), with the ±1 day lag window.**  
   1. Now just the matching logic, using the extended datasets from step 3: write new matching code, since the existing check logic (qc\_rain\_driver\_check.csv, tidal\_corroboration\_events.csv) only checks the 128 hand-logged QC dates for 11 sensors, not every day for every non-gap-tier sensor. Also add the new nearby-sensor signal (needs step 2\) and the lag-matching logic. Do this before miss rate, since miss rate can't be computed without it.  
   2. → verify: total flood-plausible days per sensor looks reasonable (not near-zero, not near-365).  
6. **Compute raw miss rate per sensor.**  
   1. Straightforward once step 5 exists — just the ratio, no correction yet.  
   2. → verify: spot-check one or two sensors by hand against their own event log.  
7. **Build the small-sample/shrinkage correction as a reusable function.**  
   1. Build it once, generically, since it'll be applied to miss rate and all three local-risk tests. Easiest to write and sanity-check against the raw miss-rate numbers you already have from step 6\.  
   2. → verify: a sensor with 1-2 opportunities gets pulled noticeably toward the network average; a sensor with 50+ barely moves.  
8. **Test A — 311-based local risk, with the overall-311-volume normalization.**  
   1. Needs the distance matrix (step 2\) and existing 311 data. Independent of Test B, can be built and checked on its own.  
   2. → verify: areas you'd expect to be high-311-flooding (known flood zones) score high.  
9. **Test B — neighbor-sensor-based local risk, with no-neighbor flagging.**  
   1. Also depends on step 4; do after Test A so you can compare the two once both exist. Uses `neighbors_df` from Step 2 (k=1 nearest sensor, capped at 3,500 ft) — not a radius/count-based lookup.  
   2. A neighbor's detection counts as positive evidence even if that neighbor is gap-tier. Only a non-gap-tier neighbor's silence counts as negative evidence. "No comparable neighbor" = nearest sensor is beyond the 3,500 ft cap. Still open: what to do when the single nearest neighbor is gap-tier and silent — fall back to 2nd-nearest, or treat as "no comparable neighbor" too (decide when actually building this step).  
   3. → verify: count how many sensors get flagged "no comparable neighbor" — make sure that's not a huge chunk of the network.  
10. **Test C — combine A and B, with the 311-only fallback for no-neighbor sensors.**  
    1. Trivial once A and B both exist — mostly just the OR logic and the fallback flag.  
    2. → verify: no-neighbor sensors are correctly marked lower-confidence in the output.  
11. **Poisson/binomial regression combining miss rate, elevation, rain, and tide/surge into the final ranking.**  
    1. This is the last piece because it needs every input above (exposure, elevation, signals) already computed and clean.  
    2. → verify: coefficients have sensible signs (e.g. higher elevation → fewer detections).  
12. **Gap-tier informational table.**  
    1. Re-run steps 5/7/8/9/10 (local risk only) on gap-tier sensors, add the caveated miss rate, output as a separate table.  
    2. → verify: gap-tier miss rates all read very high, as expected from the known feed gap.  
13. **Final ranked output \+ write-up.**  
    1. Assemble the non-gap-tier ranking, the gap-tier table, and the caveats into the deliverable format for the team.