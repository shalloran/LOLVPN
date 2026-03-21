# LOLVPN

LOLVPN is a set of defensive queries and indicators focused on (mostly consumer) VPN (and related) software on desktop operating systems. The intention here is similar in spirit to [LOLRMM](https://lolrmm.io/) (which is a nod to the original project [LOLBAS](https://lolbas-project.github.io/)).

This repo is focused on KQL in Defender (Microsoft Defender advanced hunting and related patterns) but the layout leaves room for other languages (SPL, Sigma, etc.) via the same manifest.

## Repository layout

| Path | Purpose |
|------|---------|
| `queries/<id>/` | One directory per logical query (stable `id`). Add a sibling folder for each new hunt (e.g. `consumer-vpn-multi-source`, `consumer-vpn-install-discovery`). |
| `queries/<id>/manifest.yaml` | Title, description, platforms, tables, MITRE tags, tuning notes, and `implementations.*.path` to query files. |
| `queries/<id>/query.kql` | KQL for **Defender** advanced hunting (`Timestamp`); default **summary** output. |
| `schemas/query-manifest.schema.json` | JSON Schema for `manifest.yaml` (CI or local validation). |
| `CONTRIBUTING.md` | Inclusion rules and PR expectations. |
| `.github/workflows/validate-manifests.yml` | CI: validates every `queries/*/manifest.yaml` against the JSON Schema. |
| `scripts/validate_manifests.py` | Same check locally: `pip install -r requirements-ci.txt && python scripts/validate_manifests.py`. |
| `website/` | **Static** GitHub Pages site (HTML/CSS/JS): table of queries, links to raw KQL, `api/queries.json`. |
| `scripts/build_site_data.py` | Regenerates `website/api/queries.json` from manifests (run locally or in Pages workflow). |

**Design goals:** one permalink per query (`id`), optional multi-language implementations without duplicating metadata, and exports later (e.g. generated JSON listing all manifests) without restructuring folders.

## Using a query

1. Open `queries/<id>/query.kql` in Microsoft Defender's Advanced hunting.
2. Read `manifest.yaml` for **tables**, **performance**, and **false positive** guidance.
3. Adjust time range and use **`exclude_device_name_substrings`** / **`exclude_registry_substrings`** in the query for approved corporate VPN or managed-fleet noise. Default output is a **summary** (`summarize` by device and source) so results stay under the portal row limit; see comments at the bottom of **`query.kql`** to switch to raw rows (`sort` + `take`).

If you run the same logic in **Microsoft Sentinel** / Log Analytics and your tables use **`TimeGenerated`** instead of **`Timestamp`**, rename the time column in each leg of the query to match your schema.

## Website (GitHub Pages + custom domain)

The public site mirrors the [LOLRMM](https://lolrmm.io/) pattern in a **minimal static** form: hero, contribute blurb, filterable table, and **`/api/queries.json`**.

1. **Repo settings:** **Settings → Pages → Build and deployment → Source:** *GitHub Actions* (not “Deploy from a branch”).
2. **Push to `main` (or `master`):** the [deploy github pages](.github/workflows/pages.yml) workflow builds `queries.json` and publishes the `website/` folder.
3. **Custom domain `lolvpn.org`:** `website/CNAME` is already set to `lolvpn.org`. In **Pages** settings, enter **Custom domain** `lolvpn.org`, save, then at your DNS provider add the records [GitHub documents for apex domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain) (A/AAAA for `@`) or use a **CNAME** from `www` to `<user>.github.io` if you only use `www`. Wait for DNS check to pass, then enable **Enforce HTTPS**.
4. **Profile / repo links:** edit [`website/site-config.js`](website/site-config.js) (`githubUsername`, `githubRepo`) if yours differ from `shalloran` / `shalloran/LOLVPN`.
5. **Local preview:** `pip install pyyaml && python scripts/build_site_data.py` then serve `website/` with any static server (e.g. `python -m http.server --directory website 8080`) and open `/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

See [LICENSE](LICENSE) (GPL-3.0).
