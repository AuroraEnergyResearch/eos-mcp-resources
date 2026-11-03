# Aurora report routing - global

How to find the right Aurora research report(s) for a question, in ANY market. Built from Aurora's internal product taxonomy and covers ~25 report series across 15+ markets (GB, Germany, Italy, Poland, Netherlands, Belgium, Nordics, Baltics, Iberia, Ireland, Hungary/Croatia/Serbia/Slovenia, ERCOT, MISO, CAISO, ISO-NE, Japan, Chile, Australia NEM & WEM). The taxonomy below is how you decide WHICH report you want and how to phrase the search.

## The global product architecture

Aurora's research is three bankable product families plus satellites. **Every market follows this same architecture** - only names, cadence and the grid variant differ:

1. **PRMF - "<Market> Power and Renewables Market Forecast"** (`pmf`). THE flagship, exists in essentially every covered market. Whole-market view: baseload/wholesale prices, capture prices & cannibalisation by technology, capacity & generation mix, capacity-market/CRM prices, policy & subsidy schemes, commodity (gas/carbon) + demand assumptions, renewables & thermal investment cases, Central/High/Low (+ market-specific) scenarios. *PRMF tells you what the market is worth.*
2. **Flex - "<Market> Flexible Energy Market Forecast"** (or **"Outlook"** - Germany, ISO-NE) (`pmf`). Battery/flexible-asset view: BESS investment cases (IRR by location/duration/entry-year), revenue stacks (energy trading, capacity, ancillary/balancing), gross margins, cycling/dispatch, gas recips, LDES, tolling structures. *Flex tells you what flexibility is worth.* **Built ON TOP OF the same cycle's PRMF** (report summaries state this explicitly) - pair the SAME quarter for any "flex vs market" question.
3. **Grid / Nodal / Network** (`pmf`). The locational overlay: *where value is created or destroyed by location*. The product VARIES BY MARKET STRUCTURE - see the variants table below.

Satellites: **Monthly notes/indices** (`monthly`, selected markets, e.g. Monthly GB Battery Index - realised battery performance), **Scenario analyses** (stress tests built on a flagship, e.g. GB Flexible Energy Scenario Analysis), **Strategic Insight reports** (`strategic`, ad-hoc single-theme deep dives, often multi-country), **Policy notes** (`policy`, event-driven impact analyses), **PPA benchmarks** (e.g. Australia NEM PPA Benchmark Forecast), Group Meeting decks.

## Grid-product variants by market structure

| Market structure | Grid product & focus | Verified examples |
|---|---|---|
| Fully nodal / generator-nodal (US ISOs, Chile) | Nodal prices, congestion, hub-to-node basis, curtailment, line constraints; often via Nodal Explorer software; nodal dynamics may sit INSIDE the PRMF (Chile's PRMF incorporates Marginal Cost of Losses) | Chile PRMF; US nodal products |
| Zonal + redispatch, RES-curtailment focus (DE, Iberia, Italy, Ireland) | Technical/grid curtailment volumes & %, grid-curtailed capture prices, redispatch, battery mitigation value | "German Grid Curtailment Forecast", "Ireland I-SEM Grid Constraint Forecast" |
| GB | Grid charges & network build-out, NOT uncompensated curtailment: TNUoS (locational charges), TLM (losses), Network Redispatch (constraints/siting) | "Great Britain TNUoS Forecast", "Great Britain TLM Forecast", "Great Britain Network Redispatch Forecast" |
| Australia NEM | Loss factors | "Australian Marginal Loss Factor Forecast" (MLF for all NEM solar/wind assets) |
| Japan | Grid access / injection capacity (grid-injection tool) | Japan PRMF + grid-injection analysis |

## Naming conventions

These help you phrase the `content_list_content` title search, recognise the right report, and describe it to the user:

- **Country token is usually the ADJECTIVE for European + LatAm markets**: Italian, Polish, German, Dutch, Belgian, Hungarian, Croatian, Serbian, Slovenian, Iberian, Chilean. **Noun for**: Great Britain (never "GB"), Japan, Australia, "Ireland I-SEM". **ISO acronym for the US**: ERCOT, MISO, CAISO, ISO-NE, PJM. **Region names**: Nordic (DK/FI/SE/NO in one report), Baltics (EE/LV/LT), Iberian (ES/PT), WEM (Western Australia - separate from NEM, H1/H2 cadence).
- Naming is INCONSISTENT even within one market ("Chilean PRMF" but "Chile Flexible Energy Market Forecast"; "Australia PRMF" but "Australian MLF Forecast"; Flex is "Outlook" in DE/ISO-NE, "Forecast" elsewhere; some titles use "&" for "and"). If a sensible `content_list_content` search returns nothing, retry the other country form (adjective vs noun) or drop the series' last word before concluding the report doesn't exist; the type/tag/topic filters narrow better than a longer free-text string.
- **Content ids roll over every publication cycle** - re-resolve the id for the current cycle rather than reusing a remembered one.
- Cadence: mostly quarterly with Q2/Q4 (or biannual) majors; WEM is H1/H2; monthlies monthly. "Latest" = newest publication date.
- **Within a report**: prefer an exec summary for a fast read and the full report for depth; investment cases sit near the END of Flex/PRMF reports. Prefer an xlsx data book over scraping numbers from PDF text when charting report figures.

## Topic -> product (global)

| Question is about... | Go to |
|---|---|
| Wholesale/baseload price forecast, price drivers | PRMF (+ Scenario Explorer for the series) |
| Capture prices / cannibalisation by technology | PRMF (+ Scenario Explorer technology data) |
| Subsidy/support schemes (CfD, EEG, RES auctions...) | PRMF (+ policy note if the scheme just changed) |
| Thermal economics / spark spreads | PRMF |
| Demand outlook (data centres, heat pumps, H2) | PRMF (+ strategic deep dives) |
| Capacity & generation mix buildout | PRMF |
| Capacity market / CRM clearing prices | PRMF (market-wide) + Flex (flex-asset CM revenue & de-rating) |
| PPA prices / benchmarks | PRMF; Australia: NEM PPA Benchmark Forecast |
| Battery revenue / IRR / investment case | Flex (+ Flexplorer investment cases) |
| Battery duration / co-location cases | Flex |
| Ancillary & balancing markets | Flex (detail); PRMF (overview) |
| Gas recips / engines / LDES / tolling | Flex |
| Realised battery performance | Monthly battery index (where it exists) + Flexplorer leaderboard / real-performance data |
| Nodal prices / basis risk / congestion (nodal mkts) | Grid-nodal product, or PRMF where nodal is embedded (Chile) |
| Technical curtailment / redispatch (DE, IBE, ITA, IRE) | Grid Curtailment/Constraint Forecast |
| Grid charges, losses, constraints (GB) | TNUoS / TLM / Redispatch respectively |
| Loss factors (AUS) | Marginal Loss Factor Forecast |
| Grid access / injection (JPN) | Japan grid-injection analysis |
| Where to site an asset | Grid product + Flex (IRR by location) |
| Impact of a discrete policy event | Policy note + PRMF (price deltas) + Flex (flex-asset impact) |
| Single-theme deep dive (bills, business models, hydrogen...) | Strategic Insight |

## Combination recipes (most real questions span reports)

- **Flex economics vs the underlying market** -> Flex (revenue stack, IRR narrative) + PRMF (baseload, spreads, capture, CM), SAME cycle; pull the matching series from Flexplorer and Scenario Explorer.
- **Co-located renewable + storage** -> PRMF (capture) + Flex (co-located IRR) + the market's grid product (curtailment/charges/losses).
- **Where to site a battery** -> Flex (IRR by region) + grid product (locational value/charges/losses/MLF).
- **Policy-change impact** -> policy note + PRMF + Flex.
- **Cannibalisation -> storage upside** -> PRMF (capture-price erosion) + Flex (co-located/standalone case).
- **Cross-market comparison** -> the same product family in each market, matching vintages as closely as possible; note scenario names differ by market (e.g. WEM has "Messy Transition"; Chile has dry-hydrology/constrained-transmission).

**Reproducing report text**: Aurora owns the IP on its own reports; for the user's internal use you may reproduce report text, but put reproduced passages in quotation marks and attribute them (report title + quarter + page). Prefer paraphrase for flow. The Sources-footer citation format is in the parent `SKILL.md` **Deliverables** section.
