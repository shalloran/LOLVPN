#!/usr/bin/env python3
# writes website/api/queries.json from queries/*/manifest.yaml for static pages

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
QUERIES_DIR = REPO_ROOT / "queries"
OUT_PATH = REPO_ROOT / "website" / "api" / "queries.json"


def one_line(s: str) -> str:
    return " ".join(s.split())


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

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(out)} queries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
