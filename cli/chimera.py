import argparse
import json
import os
from datetime import datetime, timezone

def _ts() -> str:
"""UTC timestamp suitable for folder names, e.g. 20251002T135901Z."""
return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def _ensure_dir(path: str) -> None:
os.makedirs(path, exist_ok=True)

def run_intent(args: argparse.Namespace) -> int:
"""Emit prompt.audit.json for the given goal."""
ts = _ts()
run_id = args.run_id or ts
out_dir = os.path.join("artifacts", ts, run_id)
_ensure_dir(out_dir)

```
doc = {
    "run_id": run_id,
    "goal": args.goal,
    "DoD": args.dod or "",
    "constraints": args.constraint or [],
    "risks": args.risk or [],
    "glossary_keys": args.glossary or [],
}

out_path = os.path.join(out_dir, "prompt.audit.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2, ensure_ascii=False)

print(out_path)
return 0
```

def run_context(args: argparse.Namespace) -> int:
"""Emit a minimal context.bundle.json scaffold."""
ts = _ts()
run_id = args.run_id or ts
out_dir = os.path.join("artifacts", ts, run_id)
_ensure_dir(out_dir)

```
bundle = {"run_id": run_id, "excerpts": [], "notes": ""}
out_path = os.path.join(out_dir, "context.bundle.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(bundle, f, indent=2, ensure_ascii=False)

print(out_path)
return 0
```

def run_plan(args: argparse.Namespace) -> int:
"""Emit a minimal code.plan.json scaffold (ops to be populated by Architect)."""
ts = _ts()
run_id = args.run_id or ts

```
# Try to reuse run_id from an existing prompt.audit.json if provided
if args.from_intent and os.path.exists(args.from_intent):
    try:
        with open(args.from_intent, "r", encoding="utf-8") as f:
            doc = json.load(f)
            run_id = doc.get("run_id", run_id)
    except Exception:
        # Best-effort; silently continue if unreadable
        pass

out_dir = os.path.join("artifacts", ts, run_id)
_ensure_dir(out_dir)

plan = {
    "run_id": run_id,
    "ops": [],  # Architect will populate atomic ops with selectors + expect_sha
}

out_path = os.path.join(out_dir, "code.plan.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(plan, f, indent=2, ensure_ascii=False)

print(out_path)
return 0
```

def main() -> int:
parser = argparse.ArgumentParser(prog="chimera", description="Chimera CLI")
sub = parser.add_subparsers(dest="cmd", required=True)

```
# intent
p_intent = sub.add_parser("intent", help="Emit prompt.audit.json for the given goal")
p_intent.add_argument("goal", help="High-level intent/goal statement")
p_intent.add_argument("--dod", help="Definition of Done (free text)")
p_intent.add_argument("--constraint", action="append", help="Constraint (repeatable)")
p_intent.add_argument("--risk", action="append", help="Risk (repeatable)")
p_intent.add_argument("--glossary", action="append", help="Glossary key (repeatable)")
p_intent.add_argument("--run-id", dest="run_id", help="Override run_id (defaults to timestamp)")
p_intent.set_defaults(func=run_intent)

# context
p_ctx = sub.add_parser("context", help="Emit context.bundle.json scaffold")
p_ctx.add_argument("--run-id", dest="run_id", help="Override run_id (defaults to timestamp)")
p_ctx.set_defaults(func=run_context)

# plan
p_plan = sub.add_parser("plan", help="Emit code.plan.json scaffold")
p_plan.add_argument("--from-intent", dest="from_intent", help="Path to prompt.audit.json to reuse run_id")
p_plan.add_argument("--run-id", dest="run_id", help="Override run_id (defaults to timestamp or intent)")
p_plan.set_defaults(func=run_plan)

args = parser.parse_args()
return args.func(args)
```

if **name** == "**main**":
raise SystemExit(main())
