# What the finished page contains

Consult when the user asks what the page offers, or to explain a notice. The page is one self-contained HTML file: data embedded in a compact columnar layout (values unaltered), Chart.js 4.4.1 embedded (MIT, `assets/chart.umd.min.js`), no web font and no outside request, so it works offline and on networks that block CDNs. Expect about 205 KB plus about 20 KB per scenario (about 380 KB for 4 entries, about 590 KB for 18). If the charting library fails to run, the page says so.

## Notices (the HTML opens with these)

- Always: a lightweight annual comparison, designed for up to 24 scenarios (each price zone counts as one; easiest to read at 8 to 10 or fewer).
- When relevant: skipped scenarios; missing files; more than 18 entries; different year ranges between scenarios; scenarios reporting only some years; one merged currency note when currencies differ (values not converted, one shared axis, so line heights are not comparable across currencies).

## Charts

- **Baseload price**: one line per scenario on one shared year grid (earliest to latest year across all scenarios), so hovering compares the same year across scenarios even when they start or end in different years. A scenario has no point outside its own years. Where a scenario reports only some years (for example every fifth), those years get markers and a straight line joins them for legibility; a notice says the line is a drawing aid and hovering shows reported years only, never an interpolated value.
- **Technology outputs**: a *Chart data* dropdown (capture price curtailed-below-zero, uncurtailed capture price, curtailment rate below zero) above the *Line colour* toggle, then a tab per technology with data plus "All technologies". Single-technology tabs use the Aurora group colour; "All technologies" uses subgroup colours where Subgroup differs from Group (Fixed vs Tracking solar PV). Lines open coloured by scenario, each scenario with its own marker. A By scenario / By technology toggle appears on the technology chart and in the scenario panel, kept in sync.
- **Capacity and generation**: controls *Chart data* (Capacity / Generation), *Chart type*, *Line colour* (over-time view only), then a Technology dropdown or a Year slider.
  - *All years, by single technology*: one line per scenario. A note appears when lines overlap because scenarios report identical values (common for capacity across Weather Years) or when every value is 0.
  - *Single year, by all technology*: one stacked bar per scenario in Aurora technology colours, for the slider year (opening on the first year every selected scenario reports). Negative values (net imports, storage charging) draw left of zero. A scenario with no data that year is labelled "no data for YEAR" and named in a note; technologies that are 0 or unreported that year are listed separately. Tested up to 24 entries.
- **Compare another variable**: a chart for any other annual system output, grouped as in Origin's dashboard tabs.

## Scenarios panel (right-hand side, scrolls independently)

Each scenario shows a colour swatch, marker, name and copyable scenario ID. Click to show or hide; double-click to show only that scenario; *Select all / Deselect all* at the top; swatch to recolour; reset colours; show or hide markers. Zone entries sit under one scenario heading (name and ID once) with short zone codes; a heading shows or hides all its zones, and when scenarios share zone codes a row of zone buttons shows or hides the same zone in every scenario. Skipped scenarios are named in the top banner.

## Other

- A **copy button** on every chart copies the visible scenarios' values as tab-separated text for Excel, with a title row (units) and a source line; hidden scenarios are left out.
- Dark theme by default, and a light theme, both using Aurora Substrate v2.1.0 tokens (canvas, elevated and overlay surfaces, text, yellow primary, chart axis and grid colours, 7px card radius; values copied into the template, nothing imported), with a Light mode toggle in the header. The page is a single scrolling page with no top navigation.
- **Axis titles**: when every scenario uses the same currency code, price axes read like Origin Outputs Explorer (`GBP per MWh (cal year 2025 avg real)`, or `(Jan 2025 real)` for monthly-average currencies), and the same rule applies to other price units (`GBP per kW`, `GBP per tonne`). When codes differ, axes read `Currency per MWh` and each tooltip line states that scenario's currency in full.
- Chart styling follows Substrate's Highcharts line charts, measured from a rendered Substrate chart: 2px straight lines (3px on hover), faint horizontal gridlines with a brighter zero line, a single muted x-axis line, 12px Lato-first chart font, and tooltips with a small header and bold values.
- Tooltips list every visible line sorted high to low, with its colour and marker shape. They are page elements, not drawn on the chart, so every line is always listed even when the tooltip is taller than the chart (18 or 24 lines, or 70+ rows on the all-technologies chart); the tooltip splits into columns only when the window is too short to hold the list.
