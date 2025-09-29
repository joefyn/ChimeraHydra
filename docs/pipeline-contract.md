\# Chimera Pipeline Contract (Artifacts, run\_id, and CI Gate)



\## Artifact Chain (authoritative)

A change is valid only if these files exist under `artifacts/<ts>/<run\_id>/` and reference the SAME `run\_id` (format: `YYYYMMDDTHHMMSSZ-<short>`):



1\) `prompt.audit.json`

2\) `code.plan.json`

3\) `codex.instructions.json`

4\) `changeset.diff` (unified diff)

5\) `gate.decision.json` (with `"decision":"approve"`)



\### Required fields (minimum)

\- Every JSON artifact MUST contain: `"run\_id": "<id>"`.

\- `code.plan.json.ops\[].selector` MUST be one of:

&nbsp; - `{ "anchor": "ANCHOR:NAME" }`  

&nbsp; - `{ "symbol": "module.Class.func" }`  

&nbsp; - `{ "line\_range": {"file":"path","start":N,"end":M} }`

\- Each op MUST include at least `"expect\_sha\_file"` and SHOULD include `"expect\_sha\_region"`.



\### Example snippets

\*\*prompt.audit.json\*\*

```json

{ "run\_id":"20250929T001500Z-abc123", "goal":"Add mm:ss HUD timer", "definition\_of\_done":\["HUD visible","pause/resume","3 tests"] }



code.plan.json

{ "run\_id":"20250929T001500Z-abc123", "ops":\[ { "selector":{"anchor":"ANCHOR:TIMER\_INJECT"}, "expect\_sha\_file":"5f2b…", "patch":"@@ ..." } ] }



codex.instructions.json

{ "run\_id":"20250929T001500Z-abc123", "ops":\[ { "apply\_patch": { "file":"ui/hud.py", "selector":{"anchor":"ANCHOR:TIMER\_INJECT"}, "patch":"@@ ..." } } ], "preconditions":\[{"file":"ui/hud.py","expect\_sha":"5f2b…"}], "glossary\_assertions":\["Timer","Tick"] }



gate.decision.json

{ "run\_id":"20250929T001500Z-abc123", "decision":"approve", "reasons":\[], "summary":{"tests\_failed":0,"lint\_errors":0} }



CI Gate (single required check)

The Chimera Gate job SHALL fail the PR unless ALL are true:

All five artifacts exist for the PR head commit’s run\_id.





All artifacts share the same run\_id and that run\_id appears in the PR title.





gate.decision.json.decision == "approve".





If test.report.json exists, summary.failed == 0.





The changeset.diff only touches files referenced in code.plan.json.ops.





PR title format:

&nbsp;feat(<slug>): <short description> \[run\_id: 20250929T001500Z-abc123]

Track B (Spike → Adopt)

Developer exports: git diff > spike.patch





chimera adopt spike.patch MUST synthesize prompt.audit.json + code.plan.json with selector precedence (anchor→symbol/AST→line\_range) and expect\_sha\* per op.





Then proceed: bridge → execute → gate under the same run\_id.





Logging (JSONL)

artifacts/<ts>/<run\_id>/run.log one line per phase:

{"run\_id":"20250929T001500Z-abc123","phase":"plan","duration\_ms":142,"model":"gpt-5","tokens":1830}





---



\## 3) `/AGENTS.md`

```markdown

\# AGENTS.md — Guidance for Automated Agents (Codex et al.)



\## Ground Rules

\- NEVER push to `main`. ALWAYS open a PR against `feature/\*`.

\- DO NOT edit unless a matching `code.plan.json` exists (or you are processing an adopted spike).

\- NO improvisation: if a selector is ambiguous or an `expect\_sha` mismatches, ABORT and report.



\## Expected Behaviour (Codex)

\*\*Input:\*\* `codex.instructions.json` with strict ops and pre/post conditions.  

\*\*Action:\*\* Apply ONLY the specified ops; preserve original line endings.  

\*\*Output:\*\*  

\- `changeset.diff`  

\- `lint.report.json` (summary)  

\- `test.report.json` (summary)



\## PR Template (use this format)

\*\*Title:\*\* `feat(<slug>): <short description> \[run\_id: <id>]`



\*\*Body:\*\*

\- \*\*Intent:\*\* copy `goal` from `prompt.audit.json`.

\- \*\*Artifacts:\*\* `artifacts/<ts>/<run\_id>/` (list files).

\- \*\*Checks:\*\* paste summaries from `lint.report.json` and `test.report.json`.

\- \*\*Notes:\*\* any blockers (e.g., “Precondition mismatch on ui/hud.py”).



\## Hard Stops

\- \*\*Precondition mismatch:\*\* A target file’s `expect\_sha` differs → abort with `CAUSE: precondition\_mismatch`.

\- \*\*Ambiguous selector:\*\* Anchor/symbol/AST/line\_range cannot be resolved → abort with `CAUSE: ambiguous\_selector`.

\- \*\*Anchor/API breach:\*\* Patch touches `ANCHOR:` line or public API without explicit re-plant → abort with `CAUSE: anchor\_or\_api\_breach`.



\## Failure Codes (for PR body / logs)

\- `10` invalid\_patch\_format

\- `11` file\_not\_tracked

\- `12` glossary\_violation

\- `13` anchor\_breach

\- `14` ambiguous\_selector

\- `15` sha\_unavailable

\- `16` scope\_excess

\- `99` unknown\_error



\## Track B (Adopted spike)

Process only spikes that have been adopted (`prompt.audit.json` + `code.plan.json` present with same `run\_id`). Treat like Track A thereafter.



\## run\_id Discipline

Include the same \*\*run\_id\*\* in: all artifacts, PR title/body, and commit message.



