#!/usr/bin/env bash
# Download Origin output files listed in a pipe-delimited file and verify each one.
#   <key>|system|<url>
#   <key>|tech|<url>
# <key> must match the scenario "key" in scenarios.json.
# Usage: bash fetch_downloads.sh urls.txt csv_dir
set -u
urls="$1"; dir="${2:-csv}"; mkdir -p "$dir"; fail=0
while IFS='|' read -r key kind url; do
  [ -z "${key:-}" ] && continue
  out="$dir/${key}_${kind}.csv.gz"
  curl -s -o "$out" "$url"
  head=$(zcat "$out" 2>/dev/null | head -1 | cut -c1-40)
  case "$head" in
    year,*|Year,*) echo "OK    ${key}_${kind}";;
    *) echo "FAIL  ${key}_${kind}: $(head -c 200 "$out")"; rm -f "$out"; fail=1;;
  esac
done < "$urls"
exit $fail
