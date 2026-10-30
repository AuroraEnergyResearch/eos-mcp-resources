# origin-multi-scenario-comparison-substrate

Fork of the Anthropic-managed `origin-multi-scenario-comparison` skill (copied 2026-10-22), with the output page restyled to Aurora's Substrate design system.

Differences from the original are confined to `assets/template.html` (CSS tokens, radii, Chart.js line, grid, axis and tooltip styling) and one line in `references/page_features.md`. Scripts, gates and workflow are unchanged, so merge upstream changes by diffing those two files.

Values are copied from Substrate v2.1.0 as measured from a rendered chart (see `dev/chart-style.md` at the repo root). Substrate itself is not imported or shipped. Check with the design-system owners before distributing outside Aurora.
