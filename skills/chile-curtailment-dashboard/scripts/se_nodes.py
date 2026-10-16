#!/usr/bin/env python3
"""Turn the node list of a Scenario Explorer Chile nodal scenario into nodes.csv.

Usage:
  python se_nodes.py <options.json> <nodes.csv>

options.json is the result of scenario_explorer_get_scenario_option with verbose
true for region "chl": either the whole {"results": [...]} object, one result
({"nodes": [...]}) or the bare nodes array.

nodes.csv columns: region,node,lat4,lon4   (lat/lon multiplied by 10000, integers)
Nodes without a location are skipped.
"""
import csv, json, sys


def load_nodes(path):
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, dict) and "results" in d:
        d = next((r for r in d["results"] if r.get("nodes")), {})
    if isinstance(d, dict):
        d = d.get("nodes", [])
    return d


def main(src, out):
    nodes = load_nodes(src)
    rows, skipped = [], 0
    for n in nodes:
        loc = n.get("location") or {}
        if loc.get("latitude") is None or loc.get("longitude") is None:
            skipped += 1
            continue
        rows.append([n["region"], n["node"], round(loc["latitude"] * 1e4), round(loc["longitude"] * 1e4)])
    if not rows:
        sys.exit(f"No nodes with a location found in {src}")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["region", "node", "lat4", "lon4"])
        w.writerows(sorted(rows))
    hubs = {r[0] for r in rows}
    print(f"{len(rows)} nodes with a location ({skipped} without) across {len(hubs)} hubs -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
