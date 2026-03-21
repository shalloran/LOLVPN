#!/usr/bin/env python3
# validates queries/*/manifest.yaml against schemas/query-manifest.schema.json

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "query-manifest.schema.json"
QUERIES_DIR = REPO_ROOT / "queries"


def main() -> int:
    if not SCHEMA_PATH.is_file():
        print(f"missing schema: {SCHEMA_PATH}", file=sys.stderr)
        return 1
    if not QUERIES_DIR.is_dir():
        print(f"missing queries dir: {QUERIES_DIR}", file=sys.stderr)
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    manifests = sorted(QUERIES_DIR.glob("*/manifest.yaml"))
    if not manifests:
        print("no manifests found under queries/*/manifest.yaml", file=sys.stderr)
        return 1

    failed = False
    for path in manifests:
        raw = path.read_text(encoding="utf-8")
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            failed = True
            print(f"{path}: yaml error: {e}", file=sys.stderr)
            continue
        if data is None:
            failed = True
            print(f"{path}: empty yaml", file=sys.stderr)
            continue

        errs = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if errs:
            failed = True
            print(f"{path}:", file=sys.stderr)
            for e in errs:
                loc = ".".join(str(p) for p in e.path) if e.path else "(root)"
                print(f"  {loc}: {e.message}", file=sys.stderr)

    if failed:
        return 1
    print(f"ok: {len(manifests)} manifest(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
