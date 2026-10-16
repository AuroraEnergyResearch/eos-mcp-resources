#!/usr/bin/env python3
"""Build the map geometry for the dashboard from the Scenario Explorer node list.

Usage:
  python build_geo.py <nodes.csv> <out.json>

nodes.csv columns: region,node,lat4,lon4   (written by se_nodes.py; lat/lon x 10000)

Hub areas are the nodes' nearest-node (Voronoi) cells, clipped to the coastline
and merged per hub. Transmission projects come from assets/projects.json and are
placed at substations matched by node name. No grid lines are drawn.
"""
import csv, json, math, os, re, sys
import numpy as np
from shapely.geometry import shape, Polygon, MultiPolygon, box
from shapely.ops import unary_union, transform
from scipy.spatial import Voronoi

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
HUB = json.load(open(os.path.join(ASSETS, "hubs.json"), encoding="utf-8"))
CFG = json.load(open(os.path.join(ASSETS, "projects.json"), encoding="utf-8"))

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


def main(nodes_csv, out):
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

    # projects, placed at substations matched by node name
    def find(rx):
        r = re.compile(rx, re.I)
        hit = sorted(n for n in nodes if r.search(n))
        return (hit[0], P(*nodes[hit[0]][1:])) if hit else (None, None)

    new, report = {}, []
    for p in CFG["projects"]:
        if p["type"] == "substation":
            name, xy = find(p["match"])
            if xy:
                new[p["key"]] = [[round(xy[0], 1), round(xy[1], 1)]]
                report.append(f"{p['key']:8s} {p['year']}  marker at {name}")
            else:
                report.append(f"{p['key']:8s} {p['year']}  NO NODE MATCHES '{p['match']}'")
        else:
            (n1, a1), (n2, a2) = find(p["from"]), find(p["to"])
            if a1 and a2:
                new[p["key"]] = [[round(a1[0], 1), round(a1[1], 1), round(a2[0], 1), round(a2[1], 1), 500]]
                report.append(f"{p['key']:8s} {p['year']}  link {n1} -> {n2}")
            else:
                miss = [rx for rx, a in ((p["from"], a1), (p["to"], a2)) if not a]
                report.append(f"{p['key']:8s} {p['year']}  NO NODE MATCHES {miss}")

    W, H = (LONMAX - LONMIN) * C * K, (LATMAX - LATMIN) * K
    geo = {"W": round(W, 1), "H": round(H, 1), "chile": svg_path(chile_p.simplify(0.6)),
           "neigh": svg_path(neigh_p.simplify(0.8)), "hubs": hubs, "nodes": node_out,
           "base": [], "new": new, "projects": CFG["projects"]}
    json.dump(geo, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{len(nodes)} nodes, {len(node_out)} map points, {len(hubs)} hubs")
    print("Projects:")
    for r in report:
        print("  " + r)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
