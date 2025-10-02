#!/usr/bin/env python3
"""
check-glossary.py — Step 6c minimal drift checker

Purpose: Detect glossary drift in artifacts and diffs.
- Reads policy/glossary.lock.json (required)
- Optionally reads policy/glossary.synonyms.json
- Scans a small set of files that matter:
  artifacts/**/prompt.audit.json, artifacts/**/code.plan.json,
  artifacts/**/codex.instructions.json, changeset.diff
- Emits artifacts/<ts>/<run_id>/drift.report.json with findings.

Status:
- Minimal, conservative rules. Flags only high-signal cases.
- Safe to run even if paths don’t exist (outputs pass/empty findings).
"""
from __future__ import annotations
import json, sys, os, re, glob, datetime
from typing import List, Dict

ROOT = os.getcwd()
LOCK_PATH = os.path.join(ROOT, "policy", "glossary.lock.json")
SYN_PATH  = os.path.join(ROOT, "policy", "glossary.synonyms.json")
TARGETS = [
    os.path.join(ROOT, "artifacts", "**", "prompt.audit.json"),
    os.path.join(ROOT, "artifacts", "**", "code.plan.json"),
    os.path.join(ROOT, "artifacts", "**", "codex.instructions.json"),
    os.path.join(ROOT, "changeset.diff"),
]

CAUSES = {
    "RENAME_NO_PROTOCOL": "Canonical term appears as a renamed variant without explicit protocol.",
    "ALIAS_WITHOUT_MAP":  "Alias used that is not covered by synonyms map.",
}

# Conservative variant generator (for a few common cases)
def variants(term: str) -> List[str]:
    s = term.strip()
    # Only simple transforms for now
    snake = s.lower().replace(" ", "_")
    camel = re.sub(r"[_\s]+(.)", lambda m: m.group(1).upper(), snake)
    pascal = camel[:1].upper() + camel[1:] if camel else camel
    # Deduplicate and exclude original
    vs = {snake, camel, pascal}
    vs.discard(s)
    return sorted(vs)


def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def iter_files(patterns: List[str]):
    for pat in patterns:
        for p in glob.glob(pat, recursive=True):
            if os.path.isfile(p):
                yield p


def main() -> int:
    lock = load_json(LOCK_PATH) or {"terms": []}
    terms = [t.get("term", "").strip() for t in lock.get("terms", []) if t.get("term")]

    syn = load_json(SYN_PATH) or []
    synonyms: Dict[str,str] = {s.get("alias", "").strip(): s.get("maps_to", "").strip() for s in syn if s.get("alias") and s.get("maps_to")}

    # Build a quick denylist of high-signal renamed variants for canonical terms
    deny_variants: Dict[str, List[str]] = {}
    for t in terms:
        deny_variants[t] = [v for v in variants(t) if v != t]

    findings = []

    for fp in iter_files(TARGETS):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue

        # Alias usage not mapped → finding
        for alias, canonical in synonyms.items():
            if alias and canonical and alias in text:
                # Mapped aliases are informational only; do not flag
                pass

        # Unmapped alias patterns (simple heuristic): words with spaces collapsed to camelCase
        # Only flag the specific high-signal case expect_sha → expectedSha
        if "expect_sha" in terms and re.search(r"\bexpectedSha\b", text):
            findings.append({
                "cause": "RENAME_NO_PROTOCOL",
                "where": fp,
                "from": "expect_sha",
                "to": "expectedSha",
                "hint": "Propose rename via plan CAUSE + update glossary.lock.json; require owner ack"
            })

    status = "fail" if findings else "pass"

    # Decide run_id & out path: use latest artifacts dir if present, else today timestamp
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_id = os.environ.get("CHIMERA_RUN_ID", ts)
    out_dir = os.path.join(ROOT, "artifacts", ts, run_id)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "drift.report.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"run_id": run_id, "status": status, "findings": findings}, f, indent=2)

    print(out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
