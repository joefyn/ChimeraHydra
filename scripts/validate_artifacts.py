#!/usr/bin/env python3
"""
Validate JSON artifacts against JSON Schemas.

Behavior:
- In hard-fail mode (--fail-on-invalid), exit 1 if any artifact is invalid
  or if no artifacts are found to validate, or if required schemas are missing.
- In soft mode (default), print a summary but exit 0.

All code and comments are ASCII-only.
"""

import argparse
import json
import sys
import pathlib
from jsonschema import Draft202012Validator, ValidationError
try:
    # RefResolver is deprecated but remains available in jsonschema 4.x.
    # It is used here for simple local $ref resolution.
    from jsonschema import RefResolver  # type: ignore
except Exception:  # pragma: no cover
    RefResolver = None  # Fallback if the import ever disappears

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate generated artifacts against JSON Schemas.")
    p.add_argument("--schemas-dir", default="schemas", help="Directory containing JSON schema files.")
    p.add_argument("--artifacts-dir", default="artifacts", help="Root directory containing artifact runs.")
    p.add_argument("--dialect", default="2020-12", help="Schema dialect hint (currently informational).")
    p.add_argument("--fail-on-invalid", action="store_true",
                   help="Exit non-zero on invalid artifacts or missing setup.")
    return p.parse_args()

# Map of artifact file name -> corresponding schema file name
SCHEMA_MAP = {
    "prompt.audit.json": "prompt.audit.schema.json",
    "code.plan.json": "code.plan.schema.json",
    "codex.instructions.json": "codex.instructions.schema.json",
}

def load_schemas(schemas_dir: pathlib.Path, hard: bool):
    schemas = {}
    store = {}
    for sch in sorted(set(SCHEMA_MAP.values())):
        p = schemas_dir / sch
        if not p.exists():
            print(f"missing schema: {p}")
            if hard:
                sys.exit(1)
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"schema parse error: {p}: {e}")
            if hard:
                sys.exit(1)
            else:
                continue
        schemas[sch] = obj
        # Populate store for simple $ref resolution using file URIs.
        store[p.resolve().as_uri()] = obj
    return schemas, store

def make_validator(schema_obj, schemas_dir: pathlib.Path, store):
    if RefResolver is None:
        # Fall back: no explicit resolver. This may limit $ref across files.
        return Draft202012Validator(schema_obj)
    base_uri = schemas_dir.resolve().as_uri().rstrip("/") + "/"
    return Draft202012Validator(schema_obj, resolver=RefResolver(base_uri=base_uri, store=store))

def main() -> int:
    args = parse_args()
    schemas_dir = pathlib.Path(args.schemas_dir)
    artifacts_root = pathlib.Path(args.artifacts_dir)
    hard = bool(args.fail_on_invalid)

    schemas, store = load_schemas(schemas_dir, hard)

    invalid = []
    seen = 0

    # Constrain to typical layout: artifacts/<ts>/<run_id>
    for run_dir in artifacts_root.glob("*/*"):
        if not run_dir.is_dir():
            continue
        for art_name, sch_name in SCHEMA_MAP.items():
            art_path = run_dir / art_name
            if not art_path.exists():
                continue
            seen += 1
            try:
                data = json.loads(art_path.read_text(encoding="utf-8"))
            except Exception as e:
                invalid.append((str(art_path), f"json-parse-error: {e}"))
                continue

            schema = schemas.get(sch_name)
            if not schema:
                msg = f"schema-missing: {sch_name}"
                if hard:
                    invalid.append((str(art_path), msg))
                else:
                    # In soft mode, warn but do not mark invalid.
                    print(f"warning: {msg} for {art_path}")
                continue

            validator = make_validator(schema, schemas_dir, store)
            # Collect only the first error per file for brevity.
            try:
                validator.validate(data)
            except ValidationError as e:
                invalid.append((str(art_path), f"schema: {sch_name}", f"error: {e.message}"))

    if seen == 0:
        print("no artifacts found under 'artifacts/*/*' to validate")
        if hard:
            return 1

    if invalid:
        print("INVALID ARTIFACTS DETECTED:")
        for row in invalid:
            print(" - ", *row)
        if hard:
            return 1

    print("validation: ok")
    return 0

if __name__ == "__main__":
    sys.exit(main())
