---
description: Write an implementation plan — e.g. /plan opening-book-explorer, or /plan from the cloud-sync spec
---

# Write a Plan

You write an implementation plan into `docs/plans/YYYY-MM-DD-description-of-task.md`: an ordered
set of tasks a future session can execute without re-deriving the design.

**Never use the `AskUserQuestion` tool anywhere in this command** — it is unreliable in this
terminal and truncates option text. Ask every question in plain text at the end of a turn, and end
the turn. No spacing tricks or padding.

**Never commit.** No `git add`, `git commit`, branches, or worktrees, and no commit steps inside
the plan you write.

## Instructions

### 1. Establish what is being planned

Parse `$ARGUMENTS`:

- If it names a spec (or one obviously matches in `docs/specs/`), read it in full — the spec is the *what and why*, and this plan is its *how*. Do not re-litigate its decisions; if one looks wrong, raise it rather than quietly planning around it.
- If it's a free-form description, work from that plus the conversation.
- If it's ambiguous, ask — in plain text, then end the turn.

### 2. Pre-flight (do all of this before writing a line of the plan)

This is the part that gets skipped, and it's the part that makes the plan worth having.

**Dependency scan.** Search `docs/plans/` (including `completed/` and any subdirectories),
`docs/specs/`, and `docs/research/` for work that touches the same files or systems. You are
looking for three things: work this plan needs first (`Depends on:`), work that can't start until
this lands (`Blocks:`), and work that already did some of this (in which case say so before
writing anything).

**Reuse audit.** Search the repo for components, utilities, helpers, and modules that overlap with
what's being planned, so tasks extend what exists rather than growing a parallel implementation.

<!-- PROJECT-SPECIFIC — customise for this repo; see docs/planning-standards.md § 4. -->
- Check `src/citeio/` (`client.py`, `render.py`, `helpers.py`) and `tests/fixtures/`
- Common reusable pieces: `Client._get_json` (the one request path; every API call goes through it), `render._presentation` and the run rules in `render.py` (extend them rather than adding a second renderer), the fake `urlopen` in `tests/test_client.py`, and the golden-file fixture pair
<!-- END PROJECT-SPECIFIC -->

**Documentation scan.** Find the docs in `docs/` that describe the systems being changed. They
become the final task.

**Review decision.** Decide whether the change needs a review: it does when its outcome can only be judged from live data over time (prompt text, thresholds, ranking or triage rules, dedupe heuristics, schedules, anything measured as a share or a rate); it does not when a test, a build, a page load, or a query verifies it on the day. A plan with reviews needs a baseline and predictions table and one review task per date. Then read the `Reviews` fields of the open plans in `docs/plans/` and `docs/plans/awaiting-review/`: a plan that changes a measure one of those reviews is measuring deploys after that review, and says so in `Depends on` with the words "review sequencing only". The rules are in `planning-standards.md` § 2.2.

**Read the code.** Open the files the plan will modify. A plan written without reading them
produces tasks that don't survive contact with the code.

### 3. Ask what you can't infer

If the pre-flight leaves genuine open questions — a design fork, an unclear boundary, a
scope question where two readings give materially different plans — ask them now, in plain text, as
a short numbered list, then end the turn and wait.

Do not ask what the code or docs can answer. Do not ask permission to proceed.

### 4. Write the plan

Follow `plan-template.md` in `chalkstream.dev/docs/templates/planning/`. Non-negotiables:

- **Filename:** `docs/plans/YYYY-MM-DD-description-of-task.md`, today's date, lowercase kebab-case.
- **Header list:** a bulleted list, one bullet per field: `**Date:**`, `**Status:**`, `**Scope:**`, `**Depends on:**`, `**Blocks:**`, `**Reviews:**`, `**Related:**`, plus `**Execution order:**` when this is one of a sequence. A field with more than one entry puts each entry on its own nested bullet — never joined with " · " on one line, and never as bare lines, which Markdown renders as one paragraph. `Depends on` / `Blocks` take relative links or the literal word "Nothing". `Status` starts with `Draft`. `Reviews` is `None — <why the change is verified on the day>`, or one nested bullet per review ending ` — due YYYY-MM-DD` or ` — not yet scheduled` when the date waits on a deploy.
- **Edit Summary table** immediately after the header block, with one row: `| YYYY-MM-DD | Plan created | one line on the shape of the plan |`.
- **Prose before tasks** — what's being built, what already exists that it assembles, and the decisions a reader would otherwise reverse-engineer. Not a restatement of the task list. A plan with reviews adds a **Baseline and predictions** table here (Measure, Baseline, Prediction), one row per measure the review tasks read.
- **Tasks ordered so each one leaves the project working.** Each names the files it touches, the steps, its tests, and what is observably true when it's done.
- **A final "Update Documentation" task** listing each doc that changes and what changes in it. If nothing needs documenting, keep the task and say so with the reason.
- **No commit steps.**
- **No hard line wrapping.** One paragraph, list item, or table row is one line. Do not break prose at a column width; the editor wraps on screen. See `chalkstream.dev/docs/writing-standards.md` § 6.

Tasks should be executable by a session that has read the plan and nothing else. Where a decision
was made during planning, state the decision *and* the alternative it beat — that's what stops it
being re-opened mid-execution.

### 5. Record the dependencies and the spec's state

If this plan depends on or blocks another, edit that other plan's header too, including review
sequencing. A dependency recorded on one side only is how sequencing gets lost.

When the plan was written from a spec, record the plan in that spec's header — the spec's
`Status` and `Plans` fields are how the specs index knows the spec now has a plan (see
`planning-standards.md` § 2.1):

- Add a nested bullet under `**Plans:**` linking the new plan, ending ` — active`. If the field still reads `None yet`, replace that with the bullet.
- Set `**Status:**` to `Planned`, or to `Partly implemented` if another `Plans` bullet is already `complete`. Keep any useful free text after ` — `.
- If `**Type:**` or `**Blocks:**` still carries a pointer to this plan (or to "the implementation plan"), move it into `Plans`: `Type` is the constant `Spec (what & why)`, and `Blocks` lists only other work that waits on the spec.
- Bump the spec's `**Date:**` and add an Edit Summary row: `| YYYY-MM-DD | Plan written | Implementation plan linked: <plan filename> |`.
- Link the spec under the plan's own `**Related:**` field, as the plan template shows.

Then rebuild the specs index from the repo root:

```bash
python3 /mnt/x/SynologyDrive/Development/chalkstream/chalkstream.dev/scripts/build_specs_index.py
```

The script writes `docs/specs/README.md`; never edit that file by hand.

### 6. Report

Say where the plan was written, summarise its shape in a few lines, and name anything the
pre-flight surfaced that the user should know — overlapping work already completed, a spec
decision that looks wrong, a dependency they may not have expected.

Then suggest `/critique <name>` as the next step. Do not start executing.

## Important

- A plan is a thinking artefact, not a formality. If the pre-flight shows the work is already done, or simpler than assumed, or blocked — say that instead of writing a plan around it.
- Size the plan to the work. Three tasks is a fine plan; padding one out to ten is worse than useless.
- Ground every task in files you have actually read.
- Don't plan work the user didn't ask for. Adjacent improvements go in the report, not the tasks.
- Never use `AskUserQuestion` — ask everything in plain text and wait for the reply.
