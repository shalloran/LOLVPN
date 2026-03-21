# Contributing

LOLVPN follows the spirit of [LOLBAS](https://lolbas-project.github.io/) and [LOLRMM](https://lolrmm.io/): **curated, reviewable entries**, clear metadata, and **defensive** use only.

## What belongs here

- **KQL first**: hunting or detection queries aimed at visibility into vpn-related software and activity on endpoints.
- **Future languages**: optional `implementations.spl` or `implementations.sigma` in the same manifest when you add parallel artifacts, keep one stable `id` per logical query.

## Inclusion criteria

1. **Defensive purpose**: inventory, policy checks, hunting, or detection tuning. No step-by-step offensive instructions.
2. **Named scope**: document vendor/product (e.g. Microsoft Defender for Endpoint advanced hunting) and **tables or data sources** the query expects.
3. **Honest operations**: call out **false positives**, **performance** concerns, and **license** for copied or adapted queries.
4. **Stable identity**: pick a kebab-case `id` and bump `version` when behavior or required schema changes.
5. **Schema**: each query lives under `queries/<id>/` with:
   - `manifest.yaml` — validated against `schemas/query-manifest.schema.json`
   - at least one implementation file (e.g. `query.kql`)

## Pull request checklist

- [ ] New or updated `manifest.yaml` matches the JSON Schema (GitHub Actions runs `scripts/validate_manifests.py` on PRs to `main` / `master`).
- [ ] Optional: run `python scripts/build_site_data.py` and commit `website/api/queries.json` when manifests change so the repo matches; GitHub Pages rebuilds that file on every deploy either way.
- [ ] Query runs in the documented platform (or PR describes gaps).
- [ ] `performanceNotes` and `falsePositives` are filled in truthfully.
- [ ] Indicators and comments are appropriate for a public defensive repo.

## Suggesting indicators or tools

Open an issue with the **product name**, **typical process or service names**, and **why** it should be listed (consumer vpn, enterprise vpn, etc.). For query changes, prefer a PR with the manifest and `.kql` updated together.
