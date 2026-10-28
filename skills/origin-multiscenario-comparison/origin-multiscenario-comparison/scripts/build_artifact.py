#!/usr/bin/env python3
"""
Fill assets/template.html with the payload from parse_origin_output.py, and embed Chart.js
(assets/chart.umd.min.js, v4.4.1, MIT) so the finished page is one self-contained file that
works offline and on networks that block CDNs. Claude never writes data values into the HTML by hand.

Usage: python3 build_artifact.py data.json out.html
"""
import json, sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
TEMPLATE = ASSETS / "template.html"
CHARTJS = ASSETS / "chart.umd.min.js"


def main():
    data_path, out_path = sys.argv[1], sys.argv[2]
    data = json.load(open(data_path))
    if not CHARTJS.exists():
        sys.exit(f"ERROR: {CHARTJS} is missing; the skill package is incomplete.")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    chartjs = CHARTJS.read_text(encoding="utf-8").replace("</script", "<\\/script")
    title = data.get("title", "Origin scenario comparison")
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = TEMPLATE.read_text(encoding="utf-8")
    # Replace the data first so no placeholder text inside the data can be mistaken for another marker.
    html = html.replace("__TITLE__", safe_title).replace("__DATA_JSON__", payload)
    html = html.replace("__CHARTJS__", chartjs, 1)
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
