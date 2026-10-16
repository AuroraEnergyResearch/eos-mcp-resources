# Aurora MCP resources

[![skills.sh](https://skills.sh/b/AuroraEnergyResearch/aurora-mcp-resources)](https://skills.sh/AuroraEnergyResearch/aurora-mcp-resources)

This repository contains reusable Agent Skills published by Aurora Energy Research. Each skill is kept as source under `skills/<skill-name>/` and follows the [Agent Skills specification](https://agentskills.io/specification).

## Install a skill

Use the [skills CLI](https://skills.sh/docs) to browse and install the skills you need:

```bash
npx skills add AuroraEnergyResearch/aurora-mcp-resources
```

Available skills:

- `aurora-power-market-analysis`
- `aus-battery-investment-case`
- `chile-curtailment-dashboard`
- `gb-battery-investment-case`

## Download a package

Version tags publish release assets containing one zip per skill. Download the required zip from [GitHub Releases](https://github.com/AuroraEnergyResearch/aurora-mcp-resources/releases).

To build the same packages locally:

```bash
python scripts/package_skills.py dist
```
