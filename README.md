# LOLVPN

<a href="https://lolvpn.org/" title="lolvpn.org"><img src="website/lolvpn-logo.png" alt="LOLVPN" width="120" height="120" /></a>

LOLVPN is a set of defensive queries and indicators focused on (mostly consumer) VPN (and related) software on desktop operating systems. The intention here is similar in spirit to [LOLRMM](https://lolrmm.io/) (which is a nod to the original project [LOLBAS](https://lolbas-project.github.io/)).

This repo is focused on KQL in Defender (Microsoft Defender advanced hunting and related patterns) but the layout leaves room for other languages (SPL, Sigma, etc.) via the structure.

## Using a query

1. Open `queries/<id>/query.kql` in Microsoft Defender's Advanced hunting.
2. Read `manifest.yaml` for **tables**, **performance**, and **false positive** guidance.
3. Adjust time range and use **`exclude_device_name_substrings`** / **`exclude_registry_substrings`** in the query for approved corporate VPN or managed-fleet noise. Default output is a **summary** (`summarize` by device and source) so results stay under the portal row limit, see comments at the bottom of **`query.kql`** to switch to raw output (`sort` + `take`).

If you run the same logic in **Microsoft Sentinel** / Log Analytics and your tables use **`TimeGenerated`** instead of **`Timestamp`**, rename the time column in the query and match your schema.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

See [LICENSE](LICENSE) (GPL v3).