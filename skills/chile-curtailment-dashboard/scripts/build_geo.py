#!/usr/bin/env python3
"""Build the map geometry for the dashboard from data-platform node and line extracts.

Usage:
  python build_geo.py <nodes.csv> <lines.csv> <out.json>

nodes.csv columns: region,node,lat4,lon4      (lat/lon multiplied by 10000, integers)
lines.csv columns: line,linefullname,s,t,kv   (s/t = source/target node codes)

Virtual nodes (no coordinates) must already be filtered out by the SQL.
Hub areas are the nodes' nearest-node (Voronoi) cells, clipped to the coastline
and merged per hub. New transmission projects come from assets/new_lines.json.
"""
import csv, json, math, os, re, sys
import numpy as np
from shapely.geometry import shape, Polygon, MultiPolygon, box
from shapely.ops import unary_union, transform
from scipy.spatial import Voronoi

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
HUB = json.load(open(os.path.join(ASSETS, "hubs.json"), encoding="utf-8"))
CFG = json.load(open(os.path.join(ASSETS, "new_lines.json"), encoding="utf-8"))

LATMAX, LATMIN, LONMIN, LONMAX = -17.3, -43.9, -75.2, -66.3
K = 27.0
C = math.cos(math.radians(30))


def P(lon, lat):
    return ((lon - LONMIN) * C * K, (LATMAX - lat) * K)


def proj(g):
    return transform(lambda x, y, z=None: (np.asarray((np.asarray(x) - LONMIN) * C * K),
                                           np.asarray((LATMAX - np.asarray(y)) * K)), g)


def svg_path(g):
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    out = []
    for p in polys:
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        for ring in [p.exterior] + list(p.interiors):
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in ring.coords) + "Z")
    return "".join(out)


def main(nodes_csv, lines_csv, out):
    nodes = {}
    for r in csv.DictReader(open(nodes_csv, encoding="utf-8")):
        code = r["region"].replace("CHL_", "")
        if code not in HUB or not r["lat4"]:
            continue
        nodes[r["node"]] = (code, int(float(r["lon4"])) / 1e4, int(float(r["lat4"])) / 1e4)
    hubs_present = {v[0] for v in nodes.values()}
    if hubs_present != set(HUB):
        sys.exit(f"Expected 16 hubs, got {sorted(hubs_present)}")

    feats = json.load(open(os.path.join(ASSETS, "outline.geojson"), encoding="utf-8"))["features"]
    view = box(LONMIN, LATMIN, LONMAX, LATMAX)
    chile = [shape(f["geometry"]) for f in feats if f["properties"]["name"] == "Chile"][0].intersection(view)
    neigh = unary_union([shape(f["geometry"]) for f in feats if f["properties"]["name"] != "Chile"]).intersection(view)
    chile_p, neigh_p = proj(chile).buffer(0), proj(neigh)

    # Voronoi cells of unique node locations, clipped to land, merged by hub
    pts = {}
    for code, lon, lat in nodes.values():
        x, y = P(lon, lat)
        pts.setdefault((round(x, 2), round(y, 2)), set()).add(code)
    keys = list(pts)
    far = np.array([[-3000, -3000], [3000, -3000], [-3000, 4000], [3000, 4000]])
    vor = Voronoi(np.vstack([np.array(keys), far]))
    cells = {}
    for i, k in enumerate(keys):
        reg = vor.regions[vor.point_region[i]]
        if not reg or -1 in reg:
            continue
        poly = Polygon(vor.vertices[reg]).intersection(chile_p)
        for code in pts[k]:
            cells.setdefault(code, []).append(poly)
    hubs = {}
    for code, name in HUB.items():
        g = unary_union(cells[code]).buffer(0.3).buffer(-0.3).simplify(0.5)
        xy = np.array([P(lon, lat) for c, lon, lat in nodes.values() if c == code])
        hubs[code] = {"name": name, "d": svg_path(g),
                      "cx": round(float(np.median(xy[:, 0])), 1), "cy": round(float(np.median(xy[:, 1])), 1)}

    node_out, seen = [], set()
    for code, lon, lat in nodes.values():
        x, y = P(lon, lat)
        k = (round(x, 1), round(y, 1))
        if k not in seen:
            seen.add(k)
            node_out.append([k[0], k[1], code])

    # lines
    lines = list(csv.DictReader(open(lines_csv, encoding="utf-8")))
    ids_present = {l["line"] for l in lines}
    assign = {}
    report = []
    subs = {}
    for p in CFG["projects"]:
        if p.get("type") == "substation":
            if p["node"] in nodes:
                x, y = P(*nodes[p["node"]][1:])
                subs[p["key"]] = [[round(x, 1), round(y, 1)]]
                report.append(f"{p['key']:9s} {p['year']}  substation marker at node {p['node']}")
            else:
                report.append(f"{p['key']:9s} {p['year']}  NODE {p['node']} NOT FOUND")
            continue
        matched = [i for i in p["ids"] if i in ids_present]
        if not matched and p.get("name_regex"):
            rx = re.compile(p["name_regex"])
            matched = [l["line"] for l in lines if rx.search(l.get("linefullname") or "")]
        for m in matched:
            assign[m] = p["key"]
        report.append(f"{p['key']:9s} {p['year']}  {len(matched)} line(s): {', '.join(matched) or 'NONE FOUND'}")

    base, new, pairs = [], {}, set()
    for l in lines:
        s_, t_ = l["s"], l["t"]
        if s_ not in nodes or t_ not in nodes:
            continue
        x1, y1 = P(*nodes[s_][1:])
        x2, y2 = P(*nodes[t_][1:])
        if abs(x1 - x2) + abs(y1 - y2) < 0.5:
            continue  # transformers and co-located nodes
        pair = (assign.get(l["line"], "base"),) + tuple(sorted((s_, t_)))
        if pair in pairs:
            continue  # parallel circuits / both HVDC directions
        pairs.add(pair)
        kv = int(float(l["kv"])) if l.get("kv") not in (None, "", "None") else 0
        seg = [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1), kv]
        if l["line"] in assign:
            new.setdefault(assign[l["line"]], []).append(seg)
        else:
            base.append(seg)

    new.update(subs)
    W, H = (LONMAX - LONMIN) * C * K, (LATMAX - LATMIN) * K
    geo = {"W": round(W, 1), "H": round(H, 1), "chile": svg_path(chile_p.simplify(0.6)),
           "neigh": svg_path(neigh_p.simplify(0.8)), "hubs": hubs, "nodes": node_out,
           "base": base, "new": new, "projects": CFG["projects"]}
    json.dump(geo, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(nodes)} nodes, {len(node_out)} map points, {len(base)} grid segments")
    print("New lines:")
    for r in report:
        print("  " + r)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
