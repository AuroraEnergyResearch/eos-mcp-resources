---
name: aurora-power-market-analysis
description: Power-market analyst methodology for the Aurora Energy Research MCP connector - data analysis plus routing to Aurora's written research. Use whenever the user asks to analyse, chart, or interpret electricity prices, generation, demand, capture rates, spreads, volatility, negative prices, nodal or locational prices and basis, cannibalisation, or battery/storage revenue using Aurora data - realised history (Historical Data), forecasts (Scenario Explorer), or battery/flex economics (Flexplorer) - and whenever the user asks to find or summarise an Aurora report, forecast, policy note, or "what does Aurora think about X". Aurora datasets only.
---

# Aurora Power-Market Analysis

Guidance for acting as a power-market analyst on top of the Aurora Energy Research MCP connector. The connector does data access and its tool descriptions cover the mechanics; this skill supplies the methodology, conventions, and tool-selection judgement the descriptions don't. It works across four data surfaces - Historical Data (realised), Scenario Explorer (Aurora's published forward-looking forecasts), Flexplorer (battery/flex), and Content (written research). It does not cover Origin (bespoke user-built scenarios) or Chronos (dispatch simulation); if a request truly needs those, say so rather than substituting a different surface.

Every answer built with this skill closes on two non-negotiables - an actual rendered chart when the question is chart-shaped, and a Sources footer citing every dataset and report used - see **Deliverables** at the end.

## Which tool to reach for

Always begin from the relevant discovery call so region codes, granularities, currencies, years, filename templates and identifiers are read from live metadata, not assumed.

| Capability | Tool(s) |
|---|---|
| Which Aurora product fits a request | `catalog_list_products` (routing overview), `catalog_describe_products` (a product's tools) |
| Realised prices / generation / demand: discover | `historical_list_regions` -> `historical_get_dataset_options` (data types, granularities, columns, years, URL templates) |
| Realised data: pull a series | `historical_get_download_url` (presigned CSV), then compute locally |
| Forward-looking scenarios: discover | `scenario_explorer_list_scenarios` (filter by region/name/publication month; market AND nodal come back together, told apart by `modelOutputType`) -> `scenario_explorer_get_scenario_options` (dataDefinitions, granularities, facts, years); `scenario_explorer_list_regions_and_currencies` for valid codes |
| Forward-looking scenarios: pull a series | `scenario_explorer_get_download_url` (copy the exact `dataDefinitions` filename template; nodal files use the `{nodename}` placeholder + `node_name`), then compute locally |
| Scenario comparison (Central vs High vs Low, quarter vs quarter) | pull each sensitivity with `scenario_explorer_get_download_url` and align on a shared period axis yourself |
| Battery/flex scenarios & cases: discover | `flexplorer_list_datasets` (regions + forecast scenarios + backcast benchmarks) -> `flexplorer_get_scenario` (its investment cases) -> `flexplorer_get_investment_case_options` (markets, currency options, columns, config) |
| Battery/flex: pull a case, benchmark, or realised performance | `flexplorer_get_download_url` with `dataset` = `investment_case` / `backcast_benchmark` / `real_performance` |
| Realised battery performance (leaderboards) | `flexplorer_get_leaderboard_options(region)` -> `flexplorer_get_download_url(dataset="real_performance", window=...)` |
| Find a report / "what does Aurora think about X" | `content_list_content` (free-text `search` + `content_types` / `tag_ids` / `topic_ids` / `scenario` filters), `content_list_tags` to resolve tag/topic ids, `content_list_regions` / `content_get_region_content` for a region's set |
| Read / download a report or its data book | `content_get_content` (full record) -> `content_get_content_downloads` (list files) -> `content_get_download_url` (signed URL; pick the xlsx data book with `file_type`), then fetch and read |

## Doing the analysis

- **No server-side analytics, compare, or weighting.** Duration curves, profiles, correlograms, histograms, and weighted averages (`sum(value*weight)/sum(weight)`) are computed by you from the downloaded rows - state the weight column you used.
- **Header shape differs by surface** - historical CSVs have a single header row; Scenario Explorer / Flexplorer / scenario-output files carry a units descriptor as row 2 (and technology-aggregated files add an aggregation-method row 3, pushing data to row 4). Read the structure before parsing so a descriptor row isn't treated as data.
- **Granularity discipline**: use coarse granularity (1y / 1m) for multi-year trends and comparisons; reserve sub-daily (30M / 1h / 15M) for sub-daily questions (peaks, spreads, price shapes, negative-price counts). Half-hourly across many years is a large pull - only fetch it when the question needs it, and if the only route to a figure is a heavy roll-up from granular data, say so and offer a coarser alternative before committing to it.
- **Pending data**: if a case/currency/basis hasn't been generated yet, retry the same arguments later or try an alternative currency-year, and flag the gap rather than reporting an empty result.

## Choosing how to compute a figure

- Single-number or per-year stats ("highest price", "average by year") -> aggregate the downloaded series.
- Distribution / how often a level occurs -> histogram; sorted "value vs % of time exceeded" -> duration curve.
- Average shape across a cycle (price by hour-of-day, generation by month) -> profile.
- Relationship between two series (GB vs DE prices; price vs solar) -> correlation.
- Cyclicality / seasonality of one series -> autocorrelation (for 30M data, lag 48 = 1 day, 336 = 1 week).
- A specific window of raw rows to plot -> pull just that window.

## Nodal / locational analysis

For any question touching node-level prices, hub-to-node basis, or congestion in a nodal market (ERCOT, CAISO, MISO, NYISO, PJM, ISO-NE, Chile), **read `references/nodal-analysis.md` FIRST** - detection, file layout, the zonal-basis formula and attribution limits don't generalise from the workflow above.

## Report routing - which report answers which question

For any "what does Aurora think about X" / "find, read or summarise the report on X" question, in ANY market, **read `references/aurora-reports.md` FIRST** for the product taxonomy (PRMF / Flex / Grid), the topic->product table, naming conventions, and combination recipes.

One rule holds before opening the reference - **report vs data**: "What does Aurora think / why / what's the investment case / IRR narrative" -> a REPORT (via `content_*`). "Give me the exact price/generation/revenue series" -> the DATA surfaces (Historical / Scenario Explorer / Flexplorer). Reports carry asset-level investment-case narrative the data tools don't.

## Combining data and reports

- **Offer the source choice when a question is genuinely dual-natured** ("outlook for X", "how do batteries look in market Y"): surface what exists on each side in one short message and ask BOTH (recommended) / DATA ONLY / REPORTS ONLY. Don't ask when the request is clearly one-sided - just proceed.
- **Vintage & conflict guard.** Data and reports are often different vintages. When numbers differ, show BOTH with their vintage/scenario/currency basis and explain the likely reason - never silently pick one or average them.
- **"Latest" means checking both sides** - newest report AND newest data vintage; state which is more recent and lead with it.

## Standard analyst definitions

- **Capture price**: a native per-technology column in scenario `technology` data (do not re-derive). Column name varies by market - Europe `export capture price, <ccy>/mwh`; Australia `dispatch weighted price, aud/mwh`; US ISOs `generation weighted average price, usd/mwh`; some markets have none. Confirm the real name from the scenario/dataset options before using.
- **Capture rate** = technology capture price / baseload (the market's wholesale/day-ahead column). Falling renewable capture rates over time = **cannibalisation**.
- **Baseload vs peak**: baseload = simple time-average; peak = average over an explicitly stated peak window.
- **Intraday spread** (key BESS arbitrage driver): max-min within each day - derive from sub-daily rows.
- **Volatility**: standard deviation over the chosen granularity - report the granularity alongside it.
- **Negative-price incidence**: share of periods below zero - compute from the sub-daily series and quote with period + market.
- **Load factor / utilisation**: generation / (capacity x hours) - confirm capacity from metadata. Europe/AUS report `load factor, %`; US ISOs report `capacity factor, %`.

## Aurora data conventions & pitfalls

- **Currency codes carry real/nominal + base year** (`gbp2024`, `eur2024`, and monthly bases like `gbp2024jan` = MONTHLY_AVG vs calendar-year AVG). Never compare across bases unstated. Any scenario can be rebased to any currency code - prefer native rebasing to manual FX for cross-market comparison, and pick from the currency options the connector reports.
- **Sensitivities are separate scenario records**, and capitalisation differs by surface: Scenario Explorer uses lower-case (`central`); Flexplorer uses capitalised (`Central`). Match the case the listing tool shows. Numbers differ across vintages of the "same" scenario.
- **Realised vs forecast**: Historical Data is realised; Scenario Explorer is projected. Never put them on one chart without labelling which is which, and note that realised is typically nominal while forecasts are in a real base year.
- **Investment-case data gives revenue/cost cashflows per market (£/kW), NOT IRR** - there is no capex in the export, so a true IRR needs capex assumptions from the Flex report or the user's own cost book. Average annual net revenue per kW is the honest ranking proxy; say so rather than implying the number is an IRR.
- **Scenario file shapes**: `generation` files are WIDE (one column per technology); `technology` / `technology-aggregated` files are ROW-KEYED by group/subgroup (filter to one technology). Aggregated files are PRE-weighted (they carry an aggregation-method descriptor) - do not re-weight them; state which weighting Aurora used. Monthly scenario files are deliberately partial (e.g. renewables-only capture detail) - a full monthly stack may have to be rolled up from the hourly file or taken annually.
- **`Hidden` values mean the subscription lacks access to that fact - they are NOT zeros.** If a whole column is Hidden, say so rather than reporting empty results.
- **Financial vs calendar year**: some regions (e.g. Australia) report on a financial year; Flexplorer investment-case files carry a "Financial Year" descriptor while historical files label the year as a plain integer with no marker. Check the descriptor row and state which basis a figure uses.
- **Month values are names, not numbers**: monthly (`1m`) files carry `Month` as `January`..`December`, not `1`..`12` - map them before sorting or filtering, or rows will parse wrong or drop.

## Data model varies by market - check first

Read the dataset/scenario options for the specific market before analysing - column names, currency, sub-daily granularity and even which datasets exist all vary. What stays constant: `system` and `technology` datasets exist where data is available; `technology` is row-keyed by class/group/subgroup (filter on the level you need); 1y/1m are broadly available. What varies:

- **Currency** is embedded in every price column (`gbp/mwh`, `eur/mwh`, `aud/mwh`, `usd/mwh`, ...). Never mix currencies across markets.
- **Sub-daily code** differs: GB & AUS use `30M`; DE, US ISOs & others use `1h` / `15M`. Read the available codes from the options.
- **Baseload/wholesale column** naming differs: GB `average wholesale market price`; DE `average wholesale electricity day ahead price` (+ intraday); US ISOs split day-ahead vs real-time hub prices.
- **Multi-region markets** split rows by sub-region (Australia NEM regions, US ISO zones) - filter on `region` too or you blend regions. Single-region markets (GB) have one region value.
- **Technology taxonomy** is three levels in rows (class -> group -> subgroup) and labels vary by market - read the actual labels from a sample rather than assuming (e.g. GB has Nuclear and Offshore wind; Australia has neither).

## Deliverables: chart + citations, every time

Two non-negotiables close every answer that uses this skill - not just combined or complex ones:

- **Render, don't narrate.** Any chart-shaped question (per "Choosing how to compute a figure" above) ends in an actual chart rendered in the code sandbox - a described number or a text table is not a substitute for the image. Duration curves: value (y) vs % of time exceeded (x). Correlograms: ACF (y) vs lag (x), lags annotated in time. Profiles: mean (y) vs hour/period/month (x). Label units + currency basis, market, period, granularity, and scenario + vintage on every chart and headline number. Check for `Hidden` cells or pending data (see conventions above) before plotting - a placeholder is not a zero.
- **Every number gets a source.** Data numbers cite surface + dataset + scenario/vintage + currency (e.g. "Scenario Explorer, Germany Q3 26 Central, system / 1y, EUR2025"; "Flexplorer investment_case, Great Britain Q2 26 Central, 4h/1cy SEW, GBP2024/kW grid"). Report claims cite title + quarter + page. Close with a **Sources** footer listing every dataset and report used, even for a single-figure answer.

Alongside those: state sample size / years covered and flag data gaps or pending responses rather than glossing over them; keep the user's data selection visible in the write-up so the basis is auditable.
