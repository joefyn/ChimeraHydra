# 4e — Hard‑Fail Validation (Gate)

**Goal:** Flip artifact validation from soft report to **hard fail** so invalid artifacts reject the Gate.

---

## A) What changes (summary)

1. Replace the existing **soft** validation step in `.github/workflows/chimerahydra-gate.yml` (labelled `Validate Chimera artifacts against schemas (4d, soft)`) with a **hard** variant labelled `Validate Chimera artifacts against schemas (4e, hard)`.
2. Remove any `continue-on-error: true` from that validation step.
3. Ensure the step exits non‑zero on invalid artifacts (the validator already returns proper exit codes). The downstream failure writer (9d) will publish a red legacy status.

---

## B) YAML patch (unified diff)

```diff
*** .github/workflows/chimerahydra-gate.yml
@@
-      - name: Validate Chimera artifacts against schemas (4d, soft)
-        run: |
-          python scripts/validate_artifacts.py --schemas-dir schemas --artifacts-dir artifacts --dialect 2020-12
-        continue-on-error: true
+      - name: Validate Chimera artifacts against schemas (4e, hard)
+        run: |
+          python scripts/validate_artifacts.py --schemas-dir schemas --artifacts-dir artifacts --dialect 2020-12 --fail-on-invalid
+        # Hard fail: no continue-on-error here. Any invalid artifact should fail the job.
```

> **Anchor for search:** `Validate Chimera artifacts against schemas (4d, soft)` → replace with the 4e block above.

---

## C) Validator script (create if missing)

Create `scripts/validate_artifacts.py` (idempotent safe). Exits **1** on any invalid artifact when `--fail-on-invalid` is supplied; otherwise exits **0** but prints a summary.

```python
#!/usr/bin/env python3
import argparse, json, sys, pathlib
from jsonschema import Draft202012Validator, ValidationError, RefResolver

parser = argparse.ArgumentParser()
parser.add_argument('--schemas-dir', default='schemas')
parser.add_argument('--artifacts-dir', default='artifacts')
parser.add_argument('--dialect', default='2020-12')
parser.add_argument('--fail-on-invalid', action='store_true')
args = parser.parse_args()

schemas_dir = pathlib.Path(args.schemas_dir)
artifacts_root = pathlib.Path(args.artifacts_dir)

# Map of artifact → schema file
SCHEMA_MAP = {
    'prompt.audit.json': 'prompt.audit.schema.json',
    'code.plan.json': 'code.plan.schema.json',
    'codex.instructions.json': 'codex.instructions.schema.json',
}

# Load schemas
schemas = {}
for sch in set(SCHEMA_MAP.values()):
    p = schemas_dir / sch
    if not p.exists():
        print(f"missing schema: {p}")
        if args.fail_on_invalid:
            sys.exit(1)
        else:
            print("warning: schema missing; skipping strict validation")
    else:
        with p.open('r', encoding='utf-8') as f:
            schemas[sch] = json.load(f)

invalid = []

for run_dir in artifacts_root.rglob('*'):
    if not run_dir.is_dir():
        continue
    for art_name, sch_name in SCHEMA_MAP.items():
        art_path = run_dir / art_name
        if not art_path.exists():
            continue
        try:
            data = json.loads(art_path.read_text(encoding='utf-8'))
        except Exception as e:
            invalid.append((str(art_path), f"json-parse-error: {e}"))
            continue
        schema = schemas.get(sch_name)
        if not schema:
            # No schema: treat as invalid only in fail mode
            if args.fail_on_invalid:
                invalid.append((str(art_path), f"schema-missing: {sch_name}"))
            continue
        try:
            Draft202012Validator(schema).validate(data)
        except ValidationError as e:
            invalid.append((str(art_path), f"schema: {sch_name}", f"error: {e.message}"))

if invalid:
    print("INVALID ARTIFACTS DETECTED:")
    for row in invalid:
        print(" - ", *row)
    if args.fail_on_invalid:
        sys.exit(1)

print("validation: ok")
```

---

## D) Post‑change behaviour

* On any invalid artifact, the validation step fails → job fails → **failure writer** posts a red legacy status to the PR **head SHA**.
* When all artifacts conform, the workflow proceeds normally to the success writer.

---

## E) Manual test snippet (optional, local)

* Temporarily introduce a known schema violation in a throwaway `artifacts/<ts>/<run_id>/prompt.audit.json` and run the Gate via `workflow_dispatch`. Expect a red status and step failure.

---

**Ready for paste.** Apply the YAML replacement and create the validator script. Then commit as `chore(4e): flip validation to hard‑fail`.
