---
name: chile-curtailment-dashboard
description: Chile curtailment dashboard — Aurora's animated map of solar and wind curtailment and battery capacity by hub, 2027–2035, built from the latest Chilean PRMF databook and Chile nodal scenario via the Aurora (EOS) MCP connector. Use when someone asks for this dashboard or a refresh for a new PRMF quarter, for Chilean curtailment by hub or node over time, or for a Chile battery/BESS vs curtailment visual.
---

# Chile curtailment dashboard

The output is one self-contained HTML file. Its layout, styling and calculations are fixed in the bundled scripts and template; your job is to fetch fresh inputs, run the scripts, check the render and report.

- **Top:** the year and four cards, each with the change vs the previous year: renewable generation (solar + wind + hydro + biomass), curtailed solar and wind (TWh), share of solar + wind potential curtailed (%), battery capacity (GW).
- **Left:** north-up map of Chile. Nodes of the nodal scenario are grouped into 16 hubs, shaded yellow→red by curtailed TWh and labelled. Batteries are circles sized by GW that pulse when capacity is added. Transmission projects appear in their online year: the Parinas 500/220 kV transformer (2027, a pulsing substation marker), 220 kV upgrades (2030–31, model only), the Kimal–Lo Aguirre HVDC (2032) and the Pichirropulli–Tineo line energised at 500 kV (2035).
- **Right:** play/pause, a clickable year timeline, and hubs ranked by % of their solar + wind curtailed, reordering each year.

## Requirements

- Aurora Energy Research (EOS) MCP connector with access to Chile PRMF content and the data platform.
- Python: `pip install openpyxl shapely scipy` (add `--break-system-packages` in a managed sandbox). Playwright is optional, for the visual check.
- Network access to `aer-content-production.s3.eu-west-2.amazonaws.com` for the presigned databook URL.

Copy the skill folder somewhere writable (e.g. `/home/claude/ccd` or a scratchpad) and run everything from there.

## Step 1 — Download the databook

1. `content_list_content` with `search: "Chilean Power and Renewables Market Forecast"` (newest first). Use the report the user named, else the newest. Note its exact title, e.g. "Chilean Power and Renewables Market Forecast Q3 2026".
2. `content_get_content_downloads` for that content id; the file you want is titled **"Data"** (xlsx) — "Granular Data" and the PDF are different files.
3. `content_get_download_url` with the content id, `file_title: "Data"`, `file_type: "xlsx"`, `file_language_code: "en"`, then `curl -s -o databook.xlsx "<url>"` (quote the URL; it expires in 2 hours).

## Step 2 — Parse the databook

```bash
python scripts/parse_databook.py databook.xlsx work/dash.json --scenario Central --start 2027 --end 2035
```

It prints the national series per year. Sanity-check: renewable generation rises steadily (≈75–95 TWh over 2027–35), share curtailed sits between a few % and the low teens, battery GW never falls. A warning that a hub has generation but no curtailment row means that hub is treated as 0% curtailed; pass it on to the user.

The definitions are agreed with the dashboard owner and stay as they are:
- Curtailed TWh = generation × p/(1−p), with p the scenario sheet's "Curtailment – fleet wide" % by hub for Solar PV and Onshore wind, and generation from the Zonal sheet. The Scenario Comparison tab is never a source.
- Battery capacity = the Zonal sheet's "Battery storage" GW summed over hubs. It can differ from the national row by 0.1 GW through rounding; that is expected.

## Step 3 — Pull nodes and lines from the data platform

Call `data_platform_get_query_instructions` once, then run these queries one at a time with `data_platform_execute_query` (max_rows 500).

**3a. Latest Chile nodal scenario**

```sql
SELECT s.id, s.hash, s.scenario, s.runtime, COUNT(*) AS nnodes FROM public.nodesettings ns JOIN public.nodes n ON n.id = ns.nodeid JOIN public.regions r ON r.id = n.regionid JOIN public.scenarios s ON s.id = ns.scenarioid WHERE r.region LIKE 'CHL%' AND s.scenariotype = 'NODAL' AND (s.deleted = false OR s.deleted IS NULL) GROUP BY s.id, s.hash, s.scenario, s.runtime ORDER BY s.runtime DESC LIMIT 5
```

Take the first row (most recent run; expect ~290 nodes across 16 hub regions) and keep its `id` and `scenario` name.

**3b. Nodes** (replace `<ID>`):

```sql
SELECT r.region, n.node, CAST(ns.latitude * 10000 AS BIGINT) AS lat4, CAST(ns.longitude * 10000 AS BIGINT) AS lon4 FROM public.nodesettings ns JOIN public.nodes n ON n.id = ns.nodeid JOIN public.regions r ON r.id = n.regionid WHERE ns.scenarioid = <ID> AND ns.latitude IS NOT NULL ORDER BY r.region, n.node
```

The ×10000 cast is deliberate: `ROUND(x::numeric, 4)` truncates to whole degrees on this warehouse. The latitude filter drops virtual distribution/demand nodes, which have no coordinates.

**3c. Lines:**

```sql
SELECT l.line, l.linefullname, sn.node AS s, tn.node AS t, CAST(ls.voltageinkv AS INT) AS kv FROM public.linesettings ls JOIN public.lines l ON l.id = ls.lineid JOIN public.nodes sn ON sn.id = l.sourcenodeid JOIN public.nodes tn ON tn.id = l.targetnodeid WHERE ls.scenarioid = <ID> ORDER BY l.line
```

Write every row verbatim to `work/nodes.csv` (header `region,node,lat4,lon4`) and `work/lines.csv` (header `line,linefullname,s,t,kv`) with one Python heredoc. Done when `wc -l` of each file equals the query's `row_count` + 1.

If the data platform tools are unavailable, copy `assets/fallback_nodes.csv` and `assets/fallback_lines.csv` (snapshot of "CHL Nodal FYR 05623a-NODAL", 14 Oct 2026) to those paths, and say in the report that the network is a snapshot, not the latest run.

## Step 4 — Build the map geometry

```bash
python scripts/build_geo.py work/nodes.csv work/lines.csv work/geo.json
```

It prints one row per project: a substation marker or the matched lines. Done when every project reports a marker or at least one line.

Projects live in `assets/new_lines.json`, each with its type, codes, year and the source of that year. Each project is drawn as what the model actually changes:
- **Parinas** is a transformer at an existing substation — a `substation` marker at node 22. Its 500 kV lines exist from the first model year and stay in the background grid.
- **Tineo** is the one existing Pichirropulli–Tineo line energised at 500 kV — a single `line`, not every line touching Tineo.

When a project reports "NONE FOUND" or "NODE … NOT FOUND" (the topology was renamed), find the element in `lines.csv` / `nodes.csv` by name ("Parinas500", "Pichirropulli", "Tineo", `DC_FROM_NODE…` for the HVDC), update the config, and rerun.

For a new PRMF quarter, check the years against the report's transmission assumptions slide (`content_search` for "transmission projects Central scenario Parinas Kimal Tineo") and update any that changed. Where you can, confirm each change in the nodal run's yearly line capacities (`origin_silver.<prefix>_yearlyline`) and tell the user about any mismatch.

## Step 5 — Assemble and check

```bash
python scripts/assemble.py work/dash.json work/geo.json <outputs>/chile_curtailment_dashboard.html \
  --report "<exact report title>" --nodal "<nodal scenario name from 3a>" --scenario Central
python scripts/check.py <outputs>/chile_curtailment_dashboard.html work/shot   # optional, needs playwright
```

`<outputs>` is the user-facing outputs folder (`/mnt/user-data/outputs` in the claude.ai sandbox).

The render passes when `work/shot_first.png` and `work/shot_last.png` show no JS errors, 16 shaded and labelled hubs, battery circles and a 16-row ranking, and the last year shows every project: the Parinas marker plus all new lines. If the fallback network was used, replace "(latest Chile nodal run)" in the output's footer with "(network snapshot of 14 Oct 2026)". Then share the HTML with the user (`present_files` in the claude.ai sandbox).

## Step 6 — Report back

A short prose summary:
- Report and nodal scenario used (names, dates).
- Two or three headline readings: share curtailed in the first year, its low point and the final year; the battery GW path; which hubs lead the ranking early vs late.
- Caveats: parser warnings, fallback network, projects you re-mapped or years you changed.

## Bundled files

- `scripts/parse_databook.py` — databook → `dash.json`; finds rows by label, so it survives new quarters.
- `scripts/build_geo.py` — nodes + lines → `geo.json`; hub areas are nearest-node cells clipped to the coastline.
- `scripts/assemble.py` — injects the data into `assets/template.html`.
- `scripts/check.py` — optional headless render and screenshots.
- `assets/new_lines.json` — transmission projects (lines or substation markers), codes, years and the source of each year.
- `assets/hubs.json` — region code → hub name.
- `assets/outline.geojson` — simplified Chile and neighbour outlines.
- `assets/fallback_nodes.csv`, `assets/fallback_lines.csv` — network snapshot for users without data-platform access.
