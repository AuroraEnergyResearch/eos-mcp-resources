---
name: chile-curtailment-dashboard
description: Chile curtailment dashboard — Aurora's animated map of solar and wind curtailment and battery capacity by hub, 2027–2035, built from the latest Chilean PRMF databook and the Chile nodal node list in Scenario Explorer, via the Aurora (EOS) MCP connector. Use when someone asks for this dashboard or a refresh for a new PRMF quarter, for Chilean curtailment by hub or node over time, or for a Chile battery/BESS vs curtailment visual.
---

# Chile curtailment dashboard

The output is one self-contained HTML file. Its layout, styling and calculations are fixed in the bundled scripts and template; your job is to fetch the latest databook and node list, run the scripts, check the render and report.

- **Top:** the year and four cards, each with the change vs the previous year: renewable generation (solar + wind + hydro + biomass), curtailed solar and wind (TWh), share of solar + wind potential curtailed (%), battery capacity (GW).
- **Left:** north-up map of Chile. Nodes from the Scenario Explorer Chile nodal scenario are grouped into 16 hubs, shaded yellow→red by curtailed TWh and labelled. Batteries are circles sized by GW that pulse when capacity is added. Published transmission projects appear in their online year at their substations: the Parinas 500/220 kV transformer (2027, a pulsing marker), the Kimal–Lo Aguirre HVDC (2032) and the Pichirropulli–Tineo line energised at 500 kV (2035), the last two as schematic straight links.
- **Right:** play/pause, a clickable year timeline, and hubs ranked by % of their solar + wind curtailed, reordering each year.

Every input comes from published Aurora products: the PRMF databook (Content) and the nodal node list (Scenario Explorer). The map carries no grid lines.

## Requirements

- Aurora Energy Research (EOS) MCP connector with access to Chile PRMF content and Chile nodal scenarios in Scenario Explorer.
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

## Step 3 — Get the nodes from Scenario Explorer

1. `scenario_explorer_list_scenarios` with `region_code: "chl"`. Pick the `nodal_output` Central scenario from the same quarter as the databook (e.g. "Chile Q3 26 (Central)" for the Q3 2026 report). If that quarter has none, take the newest Central nodal scenario and tell the user the quarters differ. Note its `hash` and `name`.
2. `scenario_explorer_get_scenario_options` with that `scenario_hash`, `region: "chl"`, `sensitivity: "central"`, `verbose: true`. The result is large (~100k characters) because it includes every node with its region and location. Save it as JSON — if the harness has already written it to a file, use that file; otherwise write the result to `work/se_options.json`.
3. Convert it:

```bash
python scripts/se_nodes.py work/se_options.json work/nodes.csv
```

Done when it reports nodes across 16 hubs (Q3 26 Central: 436 nodes, all with a location).

## Step 4 — Build the map geometry

```bash
python scripts/build_geo.py work/nodes.csv work/geo.json
```

It prints one row per project. Done when every project reports a marker or a link.

Projects live in `assets/projects.json`, each with its year, the source of that year, and case-insensitive regexes on node names: `match` for a `substation` marker, `from` / `to` for a `link`. Each project is drawn as what physically changes:
- **Parinas** is a transformer at an existing substation — a marker, not a line.
- **Tineo** is the existing Nueva Pichirropulli–Tineo line energised at 500 kV — one link between those two substations.

When a project reports "NO NODE MATCHES", find the substation in `work/nodes.csv` by name, update the regex, and rerun.

For a new PRMF quarter, check the years against the report's transmission assumptions slide (`content_search` for "transmission projects Central scenario Parinas Kimal Tineo") and update any that changed in `projects.json`.

## Step 5 — Assemble and check

```bash
python scripts/assemble.py work/dash.json work/geo.json <outputs>/chile_curtailment_dashboard.html \
  --report "<exact report title>" --nodal "<nodal scenario name from step 3>" --scenario Central
python scripts/check.py <outputs>/chile_curtailment_dashboard.html work/shot   # optional, needs playwright
```

`<outputs>` is the user-facing outputs folder (`/mnt/user-data/outputs` in the claude.ai sandbox).

The render passes when `work/shot_first.png` and `work/shot_last.png` show no JS errors, 16 shaded and labelled hubs, battery circles and a 16-row ranking, and the last year shows the Parinas marker and both links. Then share the HTML with the user (`present_files` in the claude.ai sandbox).

## Step 6 — Report back

A short prose summary:
- The report (title, publication date) and the Scenario Explorer nodal scenario used for the nodes, noting if their quarters differ.
- Two or three headline readings: share curtailed in the first year, its low point and the final year; the battery GW path; which hubs lead the ranking early vs late.
- Caveats: parser warnings, project regexes you changed or years you updated.

## Bundled files

- `scripts/parse_databook.py` — databook → `dash.json`; finds rows by label, so it survives new quarters.
- `scripts/se_nodes.py` — Scenario Explorer options JSON → `nodes.csv`.
- `scripts/build_geo.py` — nodes → `geo.json`; hub areas are nearest-node cells clipped to the coastline, projects placed at matched substations.
- `scripts/assemble.py` — injects the data into `assets/template.html`.
- `scripts/check.py` — optional headless render and screenshots.
- `assets/projects.json` — published transmission projects: type, node-name regexes, years and the source of each year.
- `assets/hubs.json` — region code → hub name.
- `assets/outline.geojson` — simplified Chile and neighbour outlines.
