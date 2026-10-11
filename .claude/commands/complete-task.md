---
description: Complete a task — move plan file, update reference docs, review documentation. Run after the work is reviewed.
---

# Complete Task

Final housekeeping after a plan has been implemented, tested, and code-reviewed. Does NOT commit — that's the user's job.

## Instructions

### 1. Identify the Plan File

Determine which plan was just completed:

- Check `$ARGUMENTS` first — if provided, find the matching plan in `docs/plans/` or `docs/plans/awaiting-review/`
- Otherwise, use conversation context — the plan file should have been referenced during implementation
- If ambiguous, ask the user

Then read the plan's `Reviews` field. If any bullet is `due` or `not yet scheduled`, do not complete the plan. Move it to `docs/plans/awaiting-review/` under the rules in CLAUDE.md § Where documents live (plain `mv`, keep the filename, links inside gain one `../`, every inbound reference gains `awaiting-review/` — grep the whole repo for the filename, the spec's `Plans` link included), set `Status` to `Awaiting review — <what shipped and when>`, add an Edit Summary row `| YYYY-MM-DD | Moved to awaiting-review | reviews due <dates> |`, and stop. Report what moved and what is due. A plan whose reviews are all `done` completes as below.

### 2. Move Plan to Completed

Move the plan file to `docs/plans/completed/` with **today's date** as prefix:

```
docs/plans/some-plan.md → docs/plans/completed/YYYY-MM-DD-some-plan.md
docs/plans/sub-folder/2026-03-07-quick-filter.md → docs/plans/completed/YYYY-MM-DD-quick-filter.md
docs/plans/awaiting-review/2026-03-07-quick-filter.md → docs/plans/completed/YYYY-MM-DD-quick-filter.md
```

Rules:
- Use plain `mv` (create `docs/plans/completed/` first if it doesn't exist). Not `git mv` — that stages the change, and staging is the user's job; git detects the rename at commit time either way
- Strip the original date prefix if present — the completed date replaces it
- Keep the descriptive portion of the filename
- Strip subdirectory paths — completed plans go flat into `completed/`

### 3. Clean Up Related Files

1. **Task file** — Check for a `.tasks.json` file alongside the plan (e.g. `docs/plans/some-plan.md.tasks.json`). If it exists, `rm` it. The user commits the deletion along with the move in section 2.
2. **Spec file** — Find the spec this plan implements and record the completion in its header. **The spec stays where it is — specs always stay.** A spec is standing reference for the *what and why* and outlives its plan; completion never deletes, moves, or re-dates it, and there is nothing to ask the user. Lookup order:
   1. Grep `docs/specs/` for a `Plans` bullet that links this plan (by its old path) — the reliable inverse link.
   2. Otherwise, the name match: a spec whose descriptive filename matches the plan's (e.g. plan `quick-filter` matches spec `quick-filter-design.md`), ignoring date prefixes. This covers plans written before the `Plans` field existed.
   Do not use a `../specs/` link in the plan's own header: a plan's `Related` field often links several specs.

   When the spec is found, update its header (the rules are in `planning-standards.md` § 2.1):
   - Change the plan's `Plans` bullet to end ` — complete YYYY-MM-DD` (today, the date in the new filename) and rewrite its link to the `completed/` path. Add the bullet if the spec has no `Plans` field yet, moving any plan pointer out of `Type` or `Blocks` at the same time.
   - Set `**Status:**` to `Implemented` when every `Plans` bullet is `complete` (ignoring `rejected`), and to `Partly implemented` otherwise. Keep any useful free text after ` — `.
   - Bump the spec's `**Date:**` and add an Edit Summary row: `| YYYY-MM-DD | Plan complete | <plan filename> completed |`.

   If the shipped work contradicts the spec, flag that in the Documentation Review (section 5) instead of editing the body.

   **Cross-repo case:** when nothing here matches, grep the sibling repos' `docs/specs/` folders under `/mnt/x/SynologyDrive/Development/chalkstream/` for a `Plans` bullet that links this plan by its cross-repo path. If one is found, do not edit the other repo — flag it to the user with the exact bullet to change (cross-repo stale links are flagged, not fixed). That repo's `docs/specs/README.md` shows the plan as `active` until the user updates it.

### 4. Update Reference Documents

Search for documents that link to the old plan path and update them:

1. **Other plans** — Check `Depends on:` / `Blocks:` lines in related plans that reference this one; update paths
2. **Other docs** — Grep for the old filename across `docs/` and fix any broken links
3. **Cross-repo links** — If the plan is referenced from sibling repos (grep the `docs/` folders of the other projects under `/mnt/x/SynologyDrive/Development/chalkstream/`), flag those stale links to the user rather than silently editing another repo
4. **Specs index** — Rebuild `docs/specs/README.md` from the repo root: `python3 /mnt/x/SynologyDrive/Development/chalkstream/chalkstream.dev/scripts/build_specs_index.py`. Never edit that file by hand
<!-- PROJECT-SPECIFIC: this repo keeps no standing status or roadmap doc; `CHANGELOG.md` is updated by the plan's own tasks. -->

### 5. Documentation Review

Check the plan file for an "Update Documentation" task. If it exists:
- Verify those documentation updates were actually done during implementation
- If any were missed, flag them to the user

If no documentation task exists, do a quick scan: does the implementation touch systems described in `docs/`? Flag any docs that look potentially stale.

<!-- PROJECT-SPECIFIC SECTION — see docs/planning-standards.md § 4. -->

### 5a. In-File Documentation Review

List every new Python source file introduced by this plan (use `git status` / `git diff --name-only` vs. the previous commit; exclude `tests/`, `__init__.py`, and `tests/fixtures/`). For each one, verify that it:

- Opens with a module docstring that says what the module is for and what it deliberately does not do (CLAUDE.md § In-file documentation)
- Gives every public function a docstring that names what it returns, and type hints on its signature

If any file is missing it, flag it to the user as a completion gap before the hand-off. Do not add the documentation silently here — surface the gap so the user can decide whether you should fill it in or they will.

<!-- END PROJECT-SPECIFIC SECTION -->

### 6. Completion Log

Before the hand-off, record the outcome in the plan itself (in its new `completed/` location):

- Append a subheading to the plan's **Edit History** section — create the section at the bottom of the file if it doesn't exist. Use today's date with the label "Plan complete", followed by a bullet list of any deviations or edits made during implementation (e.g. "Task 4 split into two steps; skipped the proposed helper in Task 6 — inline approach simpler"). If implementation followed the plan exactly, write a single bullet: "No deviations."
- Add a row to the **Edit Summary** table near the top (create it if it doesn't exist — same location `/critique` uses: after the header block, before the first task or divider): `| YYYY-MM-DD | Plan complete | One-line summary of deviations or "No deviations" |`

### 7. Report and Hand Off

Report what was done:
- Which file was moved and where
- Whether a task file was deleted (companion specs always stay put)
- Which reference documents were updated
- Which spec was updated and its new `Status`, or which cross-repo spec bullet needs a hand edit
- Which reviews, if any, were `done` and on what dates
- Any documentation gaps or stale cross-repo links found

Then say: **"Ready for you to commit when you're happy."**

Do NOT commit, push, or create PRs.
