# Origin data reference

## Tools used (Aurora Energy Research connector)

| Step | Tool | Notes |
|---|---|---|
| Find a project | `origin_list_projects(search=...)` | Returns project IDs. Use `search` to keep the result small. |
| Find scenarios | `origin_list_scenarios(region=..., project_id=..., search=..., limit=...)` | `region` is mandatory. `search` is a literal case-insensitive substring of name/description. Paginate with `offset` / `next_offset`. |
| Check outputs and currency | `origin_inspect_scenarios(requests=[{scenario_id, regions:[region]}])` | Returns `default_currency`, available `currency_codes`, years and download types. About 4k to 5k tokens per scenario (more when it exports many regions). Inspect every selected scenario: default currency years differ between scenarios in the same region. |
| Get download links | `origin_get_output_downloads(requests=[...])` | Max 20 requests per call. Each request: `{kind:"scenario_data", scenario_id, region, download_type, granularity:"1y", currency}`. |

Fields in each `origin_list_scenarios` record that matter here: `scenario_id`, `name`, `region`, `scenarioRunStatus` (`Complete` / `NotLaunched` / other), `scenarioOutputsAvailable`, `publishType` (`Published` / `Draft` / null for client-owned), `scenarioType` (`AURORA_SCENARIO` / `TENANTED_SCENARIO`), `project_id`.

There is no `weatherYear` value in the list result. Weather Year scenarios are identified by the name suffix `(YYYY Weather Year)`, for example `Great Britain Q2 26 (2023 Weather Year)`.

## Download types used

Both at granularity `1y` only:

- **`system`** (`{currency}-system-1y.csv`): one row per year, one column per output. First column `year`. Row 2 holds units; the currency appears in units such as `GBP/MWh`.
- **`technology`** (`{currency}-technology-1y.csv`): one row per (Year, Group, Subgroup). Columns used: `Capacity` (GW), `Generation` (TWh), `Capture price curtailed below zero`, `Uncurtailed capture price`, `Curtailment rate below zero`. Interconnector and storage generation can be negative (net imports, charging) and is shown as reported.

Do not use `technology-aggregated`; it has been seen to return an incomplete set of groups. Use `technology` and keep each (Group, Subgroup) pair as its own series.

Files are gzip-compressed regardless of the `.csv` extension. Row 1 is column names, row 2 is units, data starts at row 3.

`Curtailment rate below zero` is reported as a fraction with unit `-` (e.g. `0.015`). Show it as reported; do not multiply by 100.

Capture prices are only reported for variable renewables (on GB: Onshore wind, Offshore wind, Fixed solar PV, Tracking solar PV). Other technologies are null for every year and are excluded from the tabs.

## System column categories (for the "compare another variable" dropdown)

| Category | Columns (GB example) |
|---|---|
| Electricity prices | Baseload price, Off peak price, On peak price, Wholesale market price percentiles and standard deviation, Balancing market price columns |
| Spreads | Average daily spread 0.5h/1h/2h/4h, Clean/Dirty dark and spark spreads |
| Demand | Data centre, EV, Electric heat, Electrolyser, Total, Peak inflexible demand |
| Emissions | Carbon intensity (with/without negative emissions), Total emissions with negative emissions |
| Capacity market | Capacity market price |
| Commodity prices | Gas price, Coal price, Carbon price |

Column sets vary by region. The template builds the dropdown from the columns actually present, and places unrecognised columns under "Other".

## Download links

Links are long, case-sensitive and expire after about an hour. Write each link to `urls.txt` exactly as returned, in the same turn the tool result arrives, then run `scripts/fetch_downloads.sh` immediately. The script checks every file starts with a real CSV header and reports any that do not (an expired or mistyped link returns an XML error instead).

If a batch returns `"Rate Exceeded"` for some entries, request only the failed ones again in a smaller batch.
