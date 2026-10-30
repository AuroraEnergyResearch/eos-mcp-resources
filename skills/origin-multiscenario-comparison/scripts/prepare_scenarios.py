#!/usr/bin/env python3
"""
Validate a scenario manifest and assign each scenario a colour, marker and
line-dash so it can be told apart on every chart.

Input manifest (written by Claude from origin_list_scenarios results; keep it small):
{
  "mode": "project" | "list" | "weather_year",
  "title": "Great Britain Q2 26 - scenario comparison",
  "scenarios": [
     {"key": "central", "name": "...", "scenario_id": "...", "region": "gbr",
      "currency": "gbp2025", "run_status": "Complete", "outputs_available": true},
     ...
  ],
  "skipped": [ {"name": "...", "scenario_id": "...", "reason": "Not launched"} ]   # optional
}

- Scenarios whose run_status is not "Complete" or whose outputs_available is
  false are moved to "skipped" (they have no results to show).
- Weather Year scenarios (name ends "(YYYY Weather Year)" or "- WY YYYY") are sorted by year
  and, in weather_year mode, coloured along the Aurora grey->orange->gold
  gradient. Other modes use the categorical Aurora palette below.
- Optional per-entry fields: "group" (parent scenario name), "zone" (short zone code such as
  "SE3") and "currency_type" (from Origin's currency list, e.g. FINANCIAL_YEAR_AVG). If "group"/"zone"
  are missing but the name looks like "<scenario> \u2013 <zone>", they are inferred.
- Colours: a set of zones from one scenario gets one colour per zone. When several scenarios each
  have zones, marker and dash follow the SCENARIO; colour follows the ZONE (same zone, same colour in
  every scenario) when zone codes are shared, and the zone's position within its scenario otherwise.
- Limits (one price zone counts as one scenario): more than 24 entries is refused with exit code 2.
  More than 18 entries is refused with exit code 3 until the user has explicitly accepted the token
  cost versus the extra data (pass --tradeoff-confirmed once they have). Entries that share a currency
  base but use different real-price years (eur2021 and eur2025) are refused with exit code 4 until the user
  has chosen the year for each scenario (pass --currency-year-confirmed). Also prints currency warnings.

Usage: python3 prepare_scenarios.py manifest.json --out scenarios.json
"""
import argparse, json, re, sys

# Weather Year naming seen in Origin: "... (2023 Weather Year)" and "... - WY 2023"
WY_RES = [re.compile(r"\((\d{4})\s*Weather\s*Year\)\s*$", re.I),
          re.compile(r"[-\u2013]\s*WY\s*(\d{4})\s*$", re.I)]


def weather_year(name):
    for r in WY_RES:
        m = r.search(name)
        if m:
            return int(m.group(1))
    return None
PALETTE = ["#F59E00", "#6F8DB9", "#A6B727", "#DF5327", "#9DB1CF",
           "#E9E261", "#C8BD88", "#E1C4E1", "#B76D55", "#969696",
           "#FFCC00", "#869A21"]
POINTS = ["circle", "triangle", "rect", "rectRot", "star", "crossRot",
          "rectRounded", "cross"]
DASHES = [[], [6, 3], [2, 3], [10, 3, 2, 3]]
STOPS = [(0.0, "#838383"), (0.5, "#F59E00"), (1.0, "#FFCC00")]  # Aurora grey (visible on dark and light) -> orange -> gold
SOFT_LIMIT = 18   # above this the user must explicitly accept the token cost (pass --tradeoff-confirmed)
HARD_LIMIT = 24   # two Nordic scenarios with 12 price zones each; one price zone counts as one scenario
TOKENS_PER_ENTRY_K = 2.4   # approx. thousand tokens per entry (two download links of ~1.2k each)
TOKENS_FIXED_K = 8         # conversation, building and checking
TOKENS_PER_SCENARIO_K = 5  # looking up and inspecting one single-region scenario
TOKENS_PER_ZONED_SCENARIO_K = 9   # a scenario broken into several zones lists more regions
TOKENS_PER_FAMILY_MEMBER_K = 0.4  # a further Weather Year family member: its list record only (one member is inspected)


def estimate_k(entries, n_entries=None, family=False):
    """Rough thousand-token cost of a run: fixed + per scenario looked up + per entry downloaded.
    A Weather Year family is inspected once, so its other members cost only their list record.
    Fitted to measured runs within about 15%."""
    ids = {}
    for e in entries:
        ids[e["scenario_id"]] = ids.get(e["scenario_id"], 0) + 1
    counts = list(ids.values())
    if family and counts:
        look = (TOKENS_PER_ZONED_SCENARIO_K if counts[0] > 1 else TOKENS_PER_SCENARIO_K) \
               + TOKENS_PER_FAMILY_MEMBER_K * (len(counts) - 1)
    else:
        look = sum(TOKENS_PER_ZONED_SCENARIO_K if c > 1 else TOKENS_PER_SCENARIO_K for c in counts)
    n = len(entries) if n_entries is None else n_entries
    return TOKENS_FIXED_K + look + TOKENS_PER_ENTRY_K * n


def grad(t):
    for (t0, c0), (t1, c1) in zip(STOPS, STOPS[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
            b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
            return "#" + "".join(f"{round(x + (y - x) * u):02X}" for x, y in zip(a, b))
    return STOPS[-1][1]


def cur_label(code, ctype=None):
    m = re.match(r"^([a-z]{3})(\d{4})([a-z]{3})?$", code or "", re.I)
    if not m:
        return code or ""
    base, yr, mon = m.group(1).upper(), m.group(2), m.group(3)
    if mon:
        return f"{base} {mon.capitalize()} {yr} real"
    return f"{base} {'financial year' if ctype == 'FINANCIAL_YEAR_AVG' else 'calendar year'} {yr} real"


def split_name(name):
    """'<scenario> \u2013 <zone>' -> (scenario, zone); otherwise (None, None)."""
    if " \u2013 " in name:
        g, z = name.rsplit(" \u2013 ", 1)
        return g.strip(), z.strip()
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", default="scenarios.json")
    ap.add_argument("--max", type=int, default=HARD_LIMIT, help="maximum entries (default 24)")
    ap.add_argument("--allow-over-limit", action="store_true")
    ap.add_argument("--currency-year-confirmed", action="store_true",
                    help="the user has chosen which currency year each scenario is shown in")
    ap.add_argument("--tradeoff-confirmed", action="store_true",
                    help="the user has explicitly accepted the token cost of more than 18 entries")
    a = ap.parse_args()
    m = json.load(open(a.manifest))
    keep, skipped = [], list(m.get("skipped", []))
    for s in m["scenarios"]:
        if s.get("run_status", "Complete") != "Complete" or s.get("outputs_available") is False:
            skipped.append({"name": s["name"], "scenario_id": s["scenario_id"],
                            "reason": f"Not launched / no outputs (status: {s.get('run_status')})"})
        else:
            s["weather_year"] = weather_year(s["name"])
            keep.append(s)
    # A project folder made up entirely of weather years is treated as a Weather Year family.
    if keep and all(s["weather_year"] is not None for s in keep) and len(keep) > 1:
        m["mode"] = "weather_year"
    if m.get("mode") == "weather_year":
        keep.sort(key=lambda s: (s["weather_year"] is None, s["weather_year"] or 0))
    n = len(keep)
    if n > a.max and not a.allow_over_limit:
        print(f"ERROR: {n} entries selected (each price zone counts as one scenario). This skill supports at most "
              f"{a.max}. Ask the user to narrow the selection; nothing was written.")
        sys.exit(2)
    if n > SOFT_LIMIT and not a.tradeoff_confirmed:
        fam = m.get("mode") == "weather_year"
        est = estimate_k(keep, family=fam)
        low = estimate_k(keep, SOFT_LIMIT, family=fam)
        print(f"CONFIRMATION NEEDED: {n} entries selected, above {SOFT_LIMIT}. Estimated cost is about "
              f"{est:.0f}k tokens (about {low:.0f}k for {SOFT_LIMIT} entries); every entry adds two download links "
              f"(about {TOKENS_PER_ENTRY_K:.1f}k tokens) and one more line on every chart. Ask the user to choose "
              f"between all {n} (more data, more tokens) and narrowing to {SOFT_LIMIT} or fewer, then re-run with "
              f"--tradeoff-confirmed if they keep all {n}. Nothing was written.")
        sys.exit(3)
    # Same currency base but different real-price years (for example eur2021 and eur2025): the user must choose.
    by_base = {}
    for s_ in keep:
        c = s_.get("currency") or ""
        by_base.setdefault(c[:3], {}).setdefault(c, []).append(s_.get("group") or s_["name"])
    mixed = {b: v for b, v in by_base.items() if b and len(v) > 1}
    if mixed and not a.currency_year_confirmed:
        parts = []
        for b, v in mixed.items():
            parts.append(b.upper() + ": " + "; ".join(f"{c} ({', '.join(dict.fromkeys(n))})" for c, n in v.items()))
        print("CONFIRMATION NEEDED: scenarios use different currency years. " + " | ".join(parts) + ". Ask the user which "
              "currency year each scenario should be shown in, based on each scenario's currency_codes (one shared year, each "
              "in its own default, or a year per scenario). Update the manifest and re-run with --currency-year-confirmed. "
              "Nothing was written.")
        sys.exit(4)
    # Infer group/zone from "<scenario> \u2013 <zone>" names when not given explicitly.
    for s in keep:
        if not s.get("group") and not s.get("zone"):
            g, z = split_name(s["name"])
            if g and any(o is not s and o["scenario_id"] == s["scenario_id"] for o in keep):
                s["group"], s["zone"] = g, z
    groups = []
    for s in keep:
        if s.get("group") and s["group"] not in groups:
            groups.append(s["group"])
    zones = []
    for s in keep:
        if s.get("zone") and s["zone"] not in zones:
            zones.append(s["zone"])
    zone_repeats = any(sum(1 for s in keep if s.get("zone") == z) > 1 for z in zones)
    multi = len(groups) >= 2                                  # several scenarios, each broken into zones
    pos_in_group = {}
    for s in keep:
        if s.get("group") and s.get("zone"):
            pos_in_group[s["key"]] = sum(1 for o in keep if o.get("group") == s["group"] and keep.index(o) < keep.index(s))
    for i, s in enumerate(keep):
        if multi and s.get("zone") and s.get("group"):
            # Marker and dash follow the scenario. Colour follows the zone when zone codes are shared between
            # scenarios (same zone, same colour), otherwise the zone's position within its own scenario.
            gi = groups.index(s["group"])
            idx = zones.index(s["zone"]) if zone_repeats else pos_in_group[s["key"]]
            s["color"] = PALETTE[idx % len(PALETTE)]
            s["point_style"] = POINTS[gi % len(POINTS)]
            s["dash"] = DASHES[gi % len(DASHES)]
            continue
        if m.get("mode") == "weather_year" and n > 1:
            s["color"] = grad(i / (n - 1))
        else:
            s["color"] = PALETTE[i % len(PALETTE)]
        s["point_style"] = POINTS[i % len(POINTS)]
        s["dash"] = DASHES[(i // len(POINTS)) % len(DASHES)] if n > len(POINTS) else DASHES[i % 2]
    warnings = []
    if n > SOFT_LIMIT:
        warnings.append(f"{n} scenarios or price zones selected, above {SOFT_LIMIT}. More lines make the charts harder "
                        f"to read, and each one added download and token cost. You chose to keep all {n}.")
    currencies = sorted({s.get("currency") for s in keep})
    if len(currencies) > 1:
        bases = {(c or "")[:3] for c in currencies}
        by_cur = {}
        for s in keep:
            by_cur.setdefault(s.get("currency"), []).append(s.get("group") or s["name"])
        desc = "; ".join(f"{cur_label(c, next((x.get('currency_type') for x in keep if x.get('currency') == c), None))}: "
                         + ", ".join(dict.fromkeys(v)) for c, v in by_cur.items())
        if len(bases) > 1:
            warnings.append("Scenarios are in different currencies (" + desc + "). Values are shown as reported, not converted, "
                            "and share one axis, so line heights are not comparable between currencies.")
        else:
            warnings.append("Scenarios use different real-price years (" + desc + "). Values are shown as reported, "
                            "not restated, so levels are not strictly like for like. This follows your choice of currency year.")
    out = {"mode": m.get("mode"), "title": m.get("title", "Origin scenario comparison"),
           "scenarios": keep, "skipped": skipped, "warnings": warnings}
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"{n} entries kept, {len(skipped)} skipped -> {a.out}" + (f" | {len(groups)} scenarios x zones; marker and dash by scenario" if multi else ""))
    for s in skipped:
        print(f"  SKIPPED: {s['name']} - {s['reason']}")
    for w in warnings:
        print(f"  WARNING: {w}")
    if n == 0:
        sys.exit("No launched scenarios with outputs - nothing to compare.")


if __name__ == "__main__":
    main()
