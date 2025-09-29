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



