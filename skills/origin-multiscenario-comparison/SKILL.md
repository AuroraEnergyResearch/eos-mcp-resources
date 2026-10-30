---
name: "origin-multiscenario-comparison"
description: Aurora Substrate-styled variant of the Origin multi-scenario comparison (a fork of the anthropic-skills origin-multi-scenario-comparison skill with the page restyled to the Substrate design system, dark and light). Use this one when the user asks for the Substrate-styled comparison by name; otherwise use the original. Compare several Origin scenarios side by side in one interactive HTML, at annual (1y) level only; Origin's own dashboard compares two. Takes a project folder, scenarios named or given by ID (including their price zones), or a Weather Year family. Requires the Aurora Energy Research connector (with access to the scenarios), code execution and file creation with Python 3 (standard library only, tested on 3.12, no pip packages) and bash with curl and zcat, and network access to aer-aeres-origin-output-builder-production.s3.eu-west-2.amazonaws.com for downloads. The finished HTML is self-contained (Chart.js embedded) and opens offline in any modern browser. Supersedes origin-weather-year-comparison.
---

# Origin multi-scenario comparison

Reads the annual output files of several Origin scenarios and lays them side by side in one self-contained interactive HTML file.

## Say first

In the first reply, before fetching anything:

> This is a lightweight comparison at an **annual (yearly) level only**. Values are read directly from Origin's annual output files and displayed as they are; nothing is calculated, converted or interpolated. It is designed for up to 24 scenarios, counting each price zone as one scenario.

When the user wants monthly, quarterly, hourly or half-hourly results, point them to the Origin platform for those.

## Rules

1. **Verbatim.** Every number is a CSV cell shown as reported: units, currencies and scales stay as Origin gives them (a fraction stays a fraction). A series that is null in every year is left out of the tabs and dropdowns; a series that is 0 in every year is kept, with a note that the values are 0.
2. **Annual.** `granularity: "1y"` on every request.
3. **Technology series.** Use the `technology` download, with each (Group, Subgroup) pair as its own series.
4. **Skipped.** A scenario with `scenarioRunStatus` other than `Complete`, or `scenarioOutputsAvailable` false, has no results: it is skipped and named in chat (the HTML lists it too).
5. **Currency mismatches** are named in chat (each scenario's currency) and in the HTML. Origin restates values into the currency you request; the skill converts nothing.
6. **Professional tone.** Output is client-facing: the HTML and chat carry no internal notes, jokes or workflow commentary.

Read `references/data_reference.md` before the first Origin call. Technology colours come from `references/technology_colours.json` (group colour first, subgroup colour when the group has none).

## Gates

Three gates stop a run until the user decides. `prepare_scenarios.py` enforces each: it exits without writing anything until the matching flag is passed, and its message restates what to ask. Ask first; pass the flag only after the user's answer. The wording of each ask is in `references/gates.md`.

| Exit | Trips when | The user decides | Flag |
|---|---|---|---|
| 2 | more than 24 entries (one price zone is one entry) | which entries to drop | none; narrow the selection |
| 3 | more than 18 entries | token cost against data kept | `--tradeoff-confirmed` |
| 4 | scenarios share a currency base but default to different year codes (EUR 2021 against EUR 2025) | which currency year each scenario shows | `--currency-year-confirmed` |

Raise gate 3 at step 3 and gate 4 at step 4, both before any download.

## Workflow

### 1. Choose how to select

Ask with `ask_user_input_v0` (single select), using these exact option labels, unless the request already makes the mode clear:

- **Name of project folder**: all or some scenarios in one Origin project
- **Specific scenarios (names or IDs)**: names or scenario IDs
- **A Weather Year family based off Aurora's published Central scenario**: a base scenario and all its Weather Year variants

Ask only for what the mode needs. The project folder mode needs the folder's name, not a region (a folder can span regions). The other modes need a region only when the names leave it unclear. Region codes are lowercase (`gbr`); `origin_list_scenarios` with region `?` returns the valid list.

Done when the mode is known and its input (folder name, scenario names or IDs, or base name) is in hand.

### 2. Resolve the scenario list

Keep listing calls small: pass `region` always, and `project_id` or `search` whenever possible. Search with the **full name including brackets** (`Italy Q3 2026 (Origin Central)`) and `limit: 5`. Aurora's Published scenario (`AURORA_SCENARIO`, `publishType: Published`) has been the first result every time, while a loose search such as `Nordics Q4 26` returns 20+ client copies and weather-year variants that cost thousands of tokens. Client copies (`TENANTED_SCENARIO`), drafts and names with suffixes such as `-retracted` or `V2` are in scope only when the user asks for them.

**Project folder.** `origin_list_projects(search=<name>)`; when several folders share a name, show their descriptions and ask which. Then `origin_list_scenarios(region, project_id=<id>, limit=100)`. Origin requires a region on every call: start with the region the folder name suggests (`DEU` → `deu`) and query further regions only when the user names them. Summarise what was found in groups (final scenarios, weather years, earlier versions, test runs), flag any whose description signals a problem ("wrong input commit", "Test for Origin feature"), mark unlaunched ones as skipped, and offer sensible groups. Use a multi-select for 4 or fewer scenarios; otherwise offer groups or ask for names.

**Specific scenarios.** For IDs, inspect directly or `origin_list_scenarios(region, search=<distinctive part of the name>)`. For names, search by name. When a name matches more than one record (a Published and a Draft copy, client copies with the same name), show the matches with publish type and ID and ask which; `Published` is the answer when the user says "the published one".

**Weather Year family.** `origin_list_scenarios(region, search=<base name>, limit=100)`, then keep records named exactly `<base name> (YYYY Weather Year)` or `<base name> - WY YYYY` (the scripts recognise both). When a published Aurora scenario and a client copy share a name, take the published one and mention the copies left out. Ask whether to include all Weather Years found or a subset. When nothing matches, show the closest base names returned and ask.

**Scenarios exported under sub-regions.** Some scenarios (a Nordics run in region `nod`) have no results under their own region code; `origin_inspect_scenarios` lists the exported regions instead (`nod_dk1`, `nod_no2`, `nod_se3`, plus country-level `dnk`, `nor`, `swe`). Page through `region_offset` to list all of them and ask how to represent the scenario: by country, by bidding zone, or all exports. Each chosen sub-region is one entry named `<scenario name> – <zone>` with its own `region`; set `group` to the scenario name and `zone` to a short code (`SE3`) so the page shows the scenario once with its zones underneath. Country-level exports (`ita`, `aus`, `dnk`, `nor`, `swe`) stay out unless the user asks for them. Each zone is its own series.

**Several scenarios, each with zones** (Italy Q3 2026 and Italy Apr 25, 7 zones each). Resolve each scenario separately, list the regions each exports, and make one entry per scenario and zone, using the same `zone` codes where the zones match. The page then colours by zone, varies marker and dash by scenario, shows one heading per scenario, and offers zone buttons that show or hide the same zone in every scenario.

Done when every selected scenario has an ID, a region and a run status, unlaunched ones are on the skipped list, and zone choices are made.

### 3. Size check

Count entries: one per scenario, or per scenario and zone. Above 24 is gate 2. Above 18 is gate 3: ask now, with the numbers from `references/gates.md`.

Done when the count is 24 or fewer and, above 18, the user has chosen to keep them.

### 4. Inspect, currency and manifest

Inspect each selected scenario once with `origin_inspect_scenarios`, at most 10 scenarios per call (send larger sets in batches of 10). Always set `definition_limit: 1`: the result needs only the scenario and region summaries, and a larger limit returns pages of download definitions (20 cost about 12k tokens for a single scenario). Pass `regions: ["<region>"]` when one region is all you need; use `region_limit: 10`, plus `region_offset` for more, when the scenario may have zones. The result gives years, default currency, `currency_codes`, `currencyType` and exported regions. Each manifest entry takes its `currency` from here (or from the user's gate-4 choice) and `currency_type` from `currencyType`; financial-year codes such as `aud2023` are labelled "financial year".

**Weather Year family: inspect one member.** Inspect the first member and apply its years, default currency, `currency_codes` and exported regions to every other member, provided all members share the same non-null `publicationDate` in the list results (they were published together on one supply stack). Inspect every member when publication dates differ or are null (client copies). If a later download for a member fails on currency or region, inspect that member then. This takes an 18-member family from about 141k tokens to about 63k, and gate 4 is not raised among members that share defaults.

When scenarios share a currency base but their defaults differ, that is gate 4: ask per `references/gates.md`.

Write `manifest.json` (keys short, unique, lowercase, no spaces):

```json
{"mode": "project | list | weather_year", "title": "<Region> <vintage> - scenario comparison",
 "scenarios": [{"key": "central", "name": "...", "scenario_id": "...", "region": "gbr",
                "currency": "gbp2025", "currency_type": "CALENDAR_YEAR_AVG",
                "run_status": "Complete", "outputs_available": true}],
 "skipped": [{"name": "...", "scenario_id": "...", "reason": "Not launched"}]}
```

Zone entries add `"group": "<scenario name>"` and `"zone": "<code>"`. Then run `python3 scripts/prepare_scenarios.py manifest.json --out scenarios.json`. It drops unlaunched scenarios, orders Weather Years (a project made up entirely of them becomes a Weather Year family, with a grey-to-orange-to-gold gradient), assigns each entry a colour, marker and dash, and prints warnings. A non-zero exit is a gate.

Done when `prepare_scenarios.py` exits 0 and every warning and skipped scenario has been relayed to the user.

### 5. Download

Call `origin_get_output_downloads` with two requests per entry (`system` and `technology`, both `1y`, in the currency chosen for that scenario, with the entry's own `region`, sub-regions included), up to 20 requests per call (10 entries). In the same turn the links arrive, write them to `urls.txt` as `<key>|system|<url>` and `<key>|tech|<url>`, copying each link exactly, then run:

```
bash scripts/fetch_downloads.sh urls.txt csv
```

For any `FAIL`, request a fresh link for that file alone and fetch again. Files already downloaded earlier in the session for the same scenario, region and currency are reused. The scripts read the CSVs; keep their contents out of the conversation.

Done when every line of the fetch output reads `OK`.

### 6. Parse and build

```
python3 scripts/parse_origin_output.py csv scenarios.json --out data.json
python3 scripts/build_artifact.py data.json /mnt/user-data/outputs/<region>_<vintage>_scenario_comparison.html
```

The parser reports which technology series have data for each metric, and any missing files. The HTML comes only from `build_artifact.py`; data values enter it only through `data.json`.

Done when the HTML is written and any missing-files report has been relayed.

### 7. Deliver

Call `present_files` with the HTML. In chat, restate that values are annual and unmodified, list skipped scenarios and any currency mismatch, and stop. Describe the page's charts and controls only when asked; `references/page_features.md` lists them.

Done when the file is presented and the closing message covers those three points.
