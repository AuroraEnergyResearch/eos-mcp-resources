#!/usr/bin/env python3
"""
Read Origin `system` (1y) and `technology` (1y) CSVs for every scenario in
scenarios.json and emit one JSON payload for the HTML template.

Values are copied from the CSV cells exactly as reported. Nothing is summed,
averaged, converted or derived. Each raw (Group, Subgroup) pair is its own
technology series. Capacity and Generation are read as reported for the capacity/generation views.

Expected files: <csv_dir>/<key>_system.csv.gz and <csv_dir>/<key>_tech.csv.gz
CSV shape: row 1 column names, row 2 units, data from row 3.

Output uses a columnar layout (names stored once) to keep the HTML small.

Usage: python3 parse_origin_output.py csv_dir scenarios.json --out data.json
"""
import argparse, csv, gzip, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLOURS = json.load(open(HERE.parent / "references" / "technology_colours.json"))
TECH_METRICS = {  # CSV column -> key in payload
    "Capture price curtailed below zero": "capture_curtailed",
    "Uncurtailed capture price": "capture_uncurtailed",
    "Curtailment rate below zero": "curtailment_rate",
    "Capacity": "capacity",
    "Generation": "generation",
}
MIX_METRICS = ("capacity", "generation")


def rows(path):
    with gzip.open(path, "rt", newline="") as f:
        return [r for r in csv.reader(f)]


def num(v):
    v = (v or "").strip()
    if v in ("", "NA", "N/A", "null", "None"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def tech_colour(group, subgroup):
    if group in COLOURS["group_colours"]:
        return COLOURS["group_colours"][group], "group"
    if subgroup in COLOURS["subgroup_colours"]:
        return COLOURS["subgroup_colours"][subgroup], "subgroup"
    return COLOURS["fallback"], "fallback"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_dir")
    ap.add_argument("scenarios_json")
    ap.add_argument("--out", default="data.json")
    a = ap.parse_args()
    d = Path(a.csv_dir)
    meta = json.load(open(a.scenarios_json))
    system, system_units, tech, tech_units = {}, {}, {}, {}
    system_cols, series_meta, missing = [], {}, []

    for s in meta["scenarios"]:
        k = s["key"]
        p = d / f"{k}_system.csv.gz"
        if p.exists():
            r = rows(p)
            cols = r[0][1:]
            for c in cols:
                if c not in system_cols:
                    system_cols.append(c)
            system_units[k] = dict(zip(cols, r[1][1:]))
            system[k] = [{"year": int(float(x[0])), **{c: num(v) for c, v in zip(cols, x[1:])}}
                         for x in r[2:] if x and x[0].strip()]
        else:
            missing.append(f"{s['name']}: system file")
        p = d / f"{k}_tech.csv.gz"
        if p.exists():
            r = rows(p)
            idx = {c: i for i, c in enumerate(r[0])}
            tech_units[k] = {TECH_METRICS[c]: r[1][idx[c]] for c in TECH_METRICS if c in idx}
            by = {}
            for x in r[2:]:
                if not x or not x[0].strip():
                    continue
                g, sg = x[idx["Group"]].strip(), x[idx["Subgroup"]].strip()
                name = g if (not sg or sg == g) else f"{g} | {sg}"
                if name not in series_meta:
                    col, src = tech_colour(g, sg)
                    series_meta[name] = {"group": g, "subgroup": sg, "color": col,
                                         "subgroup_color": COLOURS["subgroup_colours"].get(sg, col),
                                         "color_source": src}
                by.setdefault(name, []).append(
                    {"year": int(float(x[0])),
                     **{v: num(x[idx[c]]) if c in idx else None for c, v in TECH_METRICS.items()}})
            tech[k] = by
        else:
            missing.append(f"{s['name']}: technology file")

    # Series with at least one non-null value, per metric (null-for-every-year => excluded)
    # A series is excluded only if it is null in every year. Zero-valued series are kept.
    def has_data(n, m):
        return any(row[m] is not None for k in tech for row in tech[k].get(n, []))
    available = {m: [n for n in series_meta if has_data(n, m)] for m in TECH_METRICS.values()}
    order = COLOURS["group_order"]
    for m in available:
        available[m].sort(key=lambda n: (order.index(series_meta[n]["group"])
                                         if series_meta[n]["group"] in order else 99, n))
    keep = set(n for v in available.values() for n in v)  # drop all-null series (not shown)
    tech = {k: {n: r for n, r in by.items() if n in keep} for k, by in tech.items()}
    series_meta = {n: m for n, m in series_meta.items() if n in keep}
    # Currency as reported in the units row of Baseload price
    unit_currency = {k: (u.get("Baseload price", "").split("/")[0] or None) for k, u in system_units.items()}

    # Columnar layout: each column name is stored once, followed by its values in year order.
    # Values are not altered; the HTML expands this back into rows when it opens.
    metric_keys = list(TECH_METRICS.values())
    system = {k: {"years": [r["year"] for r in rs],
                  "cols": [[r.get(c) for r in rs] for c in system_cols]} for k, rs in system.items()}
    tech = {k: {n: {"years": [r["year"] for r in rs], "vals": [[r[m] for r in rs] for m in metric_keys]}
                for n, rs in by.items()} for k, by in tech.items()}
    out = {**meta, "format": "columnar", "tech_metric_keys": metric_keys, "system_columns": system_cols, "system_units": system_units,
           "system": system, "technology": tech, "tech_units": tech_units,
           "tech_series_meta": series_meta, "tech_available": available,
           "unit_currency": unit_currency, "missing_files": missing}
    if len(set(v for v in unit_currency.values() if v)) > 1 and not any(
            "different currencies" in w or "different real-price" in w for w in meta.get("warnings", [])):
        out["warnings"] = out.get("warnings", []) + [
            "Reported units use different currencies: " +
            ", ".join(f"{s['name']} ({unit_currency.get(s['key'])})" for s in meta["scenarios"]) +
            ". Values are not converted and share one axis, so line heights are not comparable."]
    json.dump(out, open(a.out, "w"), separators=(",", ":"))
    print(f"Wrote {a.out}: {len(system)} scenarios, {len(system_cols)} system columns, "
          f"{len(series_meta)} technology series")
    for m, v in available.items():
        print(f"  {m}: {len(v)} series with data -> {v}")
    for x in missing:
        print(f"  MISSING: {x}")


if __name__ == "__main__":
    main()
