#!/usr/bin/env python3
"""Inject dashboard data and map geometry into the HTML template.

Usage:
  python assemble.py <dash.json> <geo.json> <out.html> --report "Chilean Power and Renewables Market Forecast Q3 2026"
                     --nodal "CHL Nodal FYR 05623a-NODAL" [--scenario Central]
"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))

ap = argparse.ArgumentParser()
ap.add_argument("dash")
ap.add_argument("geo")
ap.add_argument("out")
ap.add_argument("--report", required=True, help="Report title exactly as listed in EOS")
ap.add_argument("--nodal", required=True, help="Name of the Chile nodal scenario used for nodes and lines")
ap.add_argument("--scenario", default="Central")
a = ap.parse_args()

m = re.search(r"(Q[1-4]\s*\d{4}|(January|April|July|October|November)\s+\d{4})", a.report)
edition = m.group(1) if m else a.report
meta = {"scenario": a.scenario, "report": a.report.strip(), "edition": edition, "nodal": a.nodal}
d = json.load(open(a.dash, encoding="utf-8"))
title = f"{d['years'][0]}–{d['years'][-1]}, {a.scenario} scenario, {edition}"

t = open(os.path.join(HERE, "..", "assets", "template.html"), encoding="utf-8").read()
t = (t.replace("__DATA__", open(a.dash, encoding="utf-8").read())
      .replace("__GEO__", open(a.geo, encoding="utf-8").read())
      .replace("__META__", json.dumps(meta, ensure_ascii=False))
      .replace("__TITLE__", title))
os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
open(a.out, "w", encoding="utf-8").write(t)
print(f"Wrote {a.out} ({len(t)//1024} KB)")
