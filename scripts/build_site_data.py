#!/usr/bin/env python3
# writes website/api/queries.json from queries/*/manifest.yaml
# writes website/api/tracked-vpns.json from kql dynamic arrays + data/vpn-brands.yaml

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = REPO_ROOT / "queries"
BRANDS_PATH = REPO_ROOT / "data" / "vpn-brands.yaml"
OUT_QUERIES = REPO_ROOT / "website" / "api" / "queries.json"
OUT_TRACKED = REPO_ROOT / "website" / "api" / "tracked-vpns.json"
SIMPLE_ICONS_VERSION = "16.13.0"

# kql sources scanned for string literals (must stay in sync with query layout)
TRACKED_KQL_SOURCES: list[dict] = [
    {
        "queryId": "consumer-vpn-multi-source",
        "relativeKql": "queries/consumer-vpn-multi-source/query.kql",
        "arrays": ["vpn_indicators", "networksetup_brand_hints"],
    },
    {
        "queryId": "consumer-vpn-install-discovery",
        "relativeKql": "queries/consumer-vpn-install-discovery/query.kql",
        "arrays": ["path_tokens", "setup_names", "display_tokens"],
    },
]

def one_line(s: str) -> str:
    return " ".join(s.split())

def collect_string_literals(fragment: str) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(fragment)
    while i < n:
        if i + 1 < n and fragment[i] == "@" and fragment[i + 1] == '"':
            end = fragment.find('"', i + 2)
            if end == -1:
                break
            out.append(fragment[i + 2 : end])
            i = end + 1
            continue
        if fragment[i] == '"':
            end = fragment.find('"', i + 1)
            if end == -1:
                break
            out.append(fragment[i + 1 : end])
            i = end + 1
            continue
        i += 1
    return out

def slice_dynamic_array_body(kql: str, var_name: str) -> str | None:
    needle = f"let {var_name} = dynamic("
    idx = kql.find(needle)
    if idx == -1:
        return None
    start = kql.find("[", idx)
    if start == -1:
        return None
    depth = 0
    i = start
    while i < len(kql):
        c = kql[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return kql[start + 1 : i]
        i += 1
    return None

def lookup_keys_for_string(s: str) -> list[str]:
    t0 = s.lower()
    keys = [
        t0,
        t0.strip(),
        re.sub(r"[^a-z0-9.]+", "", t0),
        " ".join(t0.split()),
    ]
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def load_brand_catalog() -> tuple[dict[str, str], dict[str, dict]]:
    raw = yaml.safe_load(BRANDS_PATH.read_text(encoding="utf-8"))
    rows = raw.get("brands") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        print(f"invalid {BRANDS_PATH}: expected brands: list", file=sys.stderr)
        raise SystemExit(1)
    alias_to_id: dict[str, str] = {}
    by_id: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        bid = row.get("id")
        name = row.get("name")
        if not bid or not name:
            print(f"brand row missing id or name: {row!r}", file=sys.stderr)
            raise SystemExit(1)
        by_id[str(bid)] = row
        for alias in row.get("aliases") or []:
            if not isinstance(alias, str) or not alias.strip():
                continue
            for key in lookup_keys_for_string(alias):
                prev = alias_to_id.get(key)
                if prev is not None and prev != bid:
                    print(
                        f"alias key collision {key!r}: {prev!r} vs {bid!r}",
                        file=sys.stderr,
                    )
                    raise SystemExit(1)
                alias_to_id[key] = str(bid)
    return alias_to_id, by_id

def resolve_brand_id(raw_token: str, alias_to_id: dict[str, str]) -> str | None:
    for key in lookup_keys_for_string(raw_token):
        bid = alias_to_id.get(key)
        if bid is not None:
            return bid
    return None

def extract_tracked_tokens() -> tuple[list[tuple[str, str, str]], list[str]]:
    """returns [(queryId, arrayName, literal), ...] and list of error strings."""
    errors: list[str] = []
    found: list[tuple[str, str, str]] = []
    for src in TRACKED_KQL_SOURCES:
        qid = src["queryId"]
        path = REPO_ROOT / src["relativeKql"]
        if not path.is_file():
            errors.append(f"missing kql for tracked list: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for var_name in src["arrays"]:
            body = slice_dynamic_array_body(text, var_name)
            if body is None:
                errors.append(f"{qid}: no array {var_name}")
                continue
            for lit in collect_string_literals(body):
                found.append((qid, var_name, lit))
    return found, errors

def build_tracked_vpns_json() -> dict:
    alias_to_id, by_id = load_brand_catalog()
    rows, errs = extract_tracked_tokens()
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        raise SystemExit(1)

    acc: dict[str, dict] = {}
    unmapped: list[str] = []

    for query_id, array_name, lit in rows:
        bid = resolve_brand_id(lit, alias_to_id)
        if bid is None:
            unmapped.append(f"{query_id}/{array_name}: {lit!r}")
            continue
        slot = acc.setdefault(
            bid,
            {"tokens": set(), "refs": set()},
        )
        slot["tokens"].add(lit)
        slot["refs"].add((query_id, array_name))

    if unmapped:
        print("unmapped detection tokens (add aliases in data/vpn-brands.yaml):", file=sys.stderr)
        for u in sorted(set(unmapped)):
            print(f"  {u}", file=sys.stderr)
        raise SystemExit(1)

    cdn_base = (
        f"https://cdn.jsdelivr.net/npm/simple-icons@{SIMPLE_ICONS_VERSION}/icons/"
    )
    brands_out: list[dict] = []
    for bid in sorted(acc.keys(), key=lambda x: str(by_id[x].get("name", x)).lower()):
        meta = by_id[bid]
        icon = meta.get("simpleIcon")
        logo_url = None
        if isinstance(icon, str) and icon.strip():
            logo_url = f"{cdn_base}{icon.strip()}.svg"
        refs_sorted = sorted(acc[bid]["refs"], key=lambda t: (t[0], t[1]))
        brands_out.append(
            {
                "id": bid,
                "name": str(meta.get("name", bid)),
                "simpleIcon": icon if isinstance(icon, str) and icon.strip() else None,
                "logoUrl": logo_url,
                "tokens": sorted(acc[bid]["tokens"], key=lambda s: s.lower()),
                "queries": [
                    {"id": q, "array": a} for q, a in refs_sorted
                ],
            }
        )

    return {
        "simpleIconsVersion": SIMPLE_ICONS_VERSION,
        "brands": brands_out,
    }

def write_queries_json(repo: str, branch: str) -> int:
    base_raw = f"https://raw.githubusercontent.com/{repo}/{branch}"
    out: list[dict] = []
    for manifest_path in sorted(QUERIES_DIR.glob("*/manifest.yaml")):
        qid = manifest_path.parent.name
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        impl = data.get("implementations") or {}
        kql = impl.get("kql") or {}
        kql_path = kql.get("path") or "query.kql"
        out.append(
            {
                "id": data.get("id", qid),
                "version": data.get("version", ""),
                "title": data.get("title", qid),
                "description": one_line(str(data.get("description") or "")),
                "tags": data.get("tags") or [],
                "tables": data.get("tables") or [],
                "mitre": data.get("mitre") or [],
                "githubRawKql": f"{base_raw}/queries/{qid}/{kql_path}",
                "githubManifest": f"{base_raw}/queries/{qid}/manifest.yaml",
                "githubBrowse": f"https://github.com/{repo}/tree/{branch}/queries/{qid}",
            }
        )
    OUT_QUERIES.parent.mkdir(parents=True, exist_ok=True)
    OUT_QUERIES.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_QUERIES} ({len(out)} queries)")
    return len(out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", "shalloran/LOLVPN"),
        help="owner/name for github raw/browse links (forks: pass --repo or set GITHUB_REPOSITORY)",
    )
    p.add_argument(
        "--branch",
        default=os.environ.get("GITHUB_REF_NAME", "main"),
        help="branch name for raw.githubusercontent.com (ci uses GITHUB_REF_NAME)",
    )
    args = p.parse_args()
    repo = args.repo.strip()
    branch = args.branch.strip() or "main"
    if not QUERIES_DIR.is_dir():
        print(f"missing {QUERIES_DIR}", file=sys.stderr)
        return 1
    if not BRANDS_PATH.is_file():
        print(f"missing {BRANDS_PATH}", file=sys.stderr)
        return 1

    write_queries_json(repo, branch)

    tracked = build_tracked_vpns_json()
    OUT_TRACKED.parent.mkdir(parents=True, exist_ok=True)
    OUT_TRACKED.write_text(json.dumps(tracked, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_TRACKED} ({len(tracked['brands'])} brands)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
