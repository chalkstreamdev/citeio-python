# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

`citeio` is the open-source Python library that renders Cite research reports on a customer's own site. It wraps the three Cite API calls a site needs (list a project's reports, get one report, download an image), turns a report's `presentation` object into two HTML fragments (`body_html` and `sources_html`), and offers two helpers (`publishable` and `parse_datetime`). The public API is six names: `Client`, `APIError`, `body_html`, `sources_html`, `publishable`, and `parse_datetime`. Everything else is private.

The design is in the chalkstream.dev repo: [`../chalkstream.dev/docs/specs/2026-09-23-citeio-python-library.md`](../chalkstream.dev/docs/specs/2026-09-23-citeio-python-library.md). Read it before you change what the library does.

## Rules that are easy to break

- **`dependencies` in `pyproject.toml` stays empty.** The package runs on the Python 3.11+ standard library only. Adding a dependency needs a spec change.
- **Cite decides; the library renders.** Which key is the title, where a link goes, and what a report's slug is are Cite's decisions, served in the API. The library never re-decides them and never slugifies a title.
- **Nothing breaks on a new field.** The library ignores keys it does not know and renders a run it does not understand as plain text or as nothing. It never raises on Cite's output.
- **This repository is public.** No API key, no live image URL, and no GTO report goes in the code, the tests, or the fixtures.
- **The markup is pinned by `tests/fixtures/presentation.html`.** A deliberate markup change regenerates that file, and the diff is reviewed, because users style the output.

## Working in WSL

The code lives on a Windows-mounted Synology drive; Claude runs in WSL2 and the user develops on Windows.

- **Two virtualenvs, never shared.** `.venv/` at the repo root is the user's Windows venv; do not touch it. Claude's Linux venv is at `~/.venvs/citeio`. `.claude/settings.local.json` sets `UV_PROJECT_ENVIRONMENT=/home/nick/.venvs/citeio`, so plain `uv` commands target it. Rebuild it with `uv sync`.
- **Tests:** `uv run pytest -q`. **Lint:** `uv run ruff check .`. CI runs both on Python 3.11 to 3.14.
- **Sandbox:** `uv` writes to `~/.cache/uv` and the venv; both are in `sandbox.filesystem.allowWrite` in `.claude/settings.local.json`. That allowlist loads at session start, so restart the session after editing it.

## In-file documentation

Every Python module in `src/citeio/` opens with a module docstring that says what the module is for and what it deliberately does not do. Every public function has a docstring that names what it returns, and type hints on its signature. Tests and `__init__.py` are exempt.

## Working conventions — planning and documentation

### Git

- **Claude never commits** — no `git add`, `git commit`, `git push`, `git merge`, or `git reset --hard`. Work is presented for review; the user commits.
- **No branches, no worktrees.** All work happens directly on `master`.
- **Moving or deleting a document uses plain `mv` / `rm`, never `git mv` / `git rm`** — both of those stage the change, and staging is the user's job. Nothing is lost: git detects the rename at commit time either way.
- Plans must not contain commit steps.

### Asking the user questions

**Never use the `AskUserQuestion` tool.** It is unreliable in this terminal and truncates option
text. Ask in plain prose at the end of a turn — a numbered list where there are options, the
recommended one first and marked — then end the turn and wait. No spacing tricks or padding to
work around the tool's rendering; there is no tool to work around.

### Servers

- **Claude never opens a connection to a server.** No `ssh`, `scp`, `rsync`, or any command that runs on cs-app1 or another box. The sandbox blocks these calls, and the block is intended. Do not retry, do not disable the sandbox, and do not substitute a documented or guessed value for the live fact.
- **Ask Nick to run the command instead.** Give the exact command, label where it runs (server SSH), and say which part of the output you need.
- **If the missing fact blocks the task:** do every part of the work that does not depend on it, then stop and ask.
- **If the missing fact is only informational:** finish the work, then ask for the data at the end of the turn.
- Deploy scripts (`scripts/deploy.sh`, `scripts/deploy.ps1`) open an SSH session, so the same rule applies. Nick runs deploys.
- **`journalctl` on cs-app1 needs `sudo`.** Always write it as `sudo journalctl …` in a command for Nick. Without `sudo`, the command does not show the system and service logs.

### Where documents live

| Kind | Path | Date in filename |
|---|---|---|
| Implementation plan | `docs/plans/YYYY-MM-DD-description-of-task.md` | Creation date |
| Plan awaiting review | `docs/plans/awaiting-review/YYYY-MM-DD-description-of-task.md` | Creation date (unchanged by the move) |
| Completed plan | `docs/plans/completed/YYYY-MM-DD-description-of-task.md` | **Completion** date |
| Spec / design (the "what and why") | `docs/specs/YYYY-MM-DD-description-of-task.md` | Creation date |
| Research / investigation | `docs/research/YYYY-MM-DD-description.md` | Creation date |

A plan moves to `awaiting-review/` when the only work left is a scheduled review of live data (for example, a week-one read after a deploy). Plans in `docs/plans/` itself are the ones that can be executed or critiqued now. The `awaiting-review/` rules:

- Move a plan to `awaiting-review/` when its last task that is not a review is done. Its `**Status:**` becomes `Awaiting review — <deploy date and what remains>`, and its `**Reviews:**` bullets carry the dates.
- Use plain `mv`, keep the filename, and fix the links: relative links inside the plan gain one `../`, and every inbound reference (other docs, the spec's `Plans` bullet, and `docs/plans/...` paths in code comments and tests) gains `awaiting-review/`. Grep the whole repo for the filename.
- `/complete-task` on a plan with a review still `due` or `not yet scheduled` does not complete it: it moves the plan to `awaiting-review/` under these rules and stops.
- When the last review is done, `/complete-task` moves the plan from `awaiting-review/` to `completed/` as usual.
- If a review finds work to do, either write a new plan for it, or move the plan back to `docs/plans/` with the new tasks added and `Status` back to `In progress`.

Filenames are lowercase kebab-case throughout. Every document is date-prefixed — no exceptions,
including specs and research. Standing reference documents (roadmaps, code style, deployment
procedures) are *not* plans: they live at `docs/<name>.md` without a date prefix, and carry a
`**Date:**` header line that gets bumped on each edit instead.

### Writing a plan

Before writing, scan `docs/plans/` (including `completed/`), `docs/specs/`, and `docs/` for
existing material that touches the same files or systems. Then follow
`docs/templates/planning/plan-template.md` in the chalkstream.dev repo. In particular:

- The header is a bulleted list, one bullet per field. It must carry `**Depends on:**` and `**Blocks:**` bullets — link related plans by relative path, or state "Nothing". When a plan is one of a sequence, add an `**Execution order:**` bullet. A field with more than one entry puts each entry on its own nested bullet, never joined with " · " on one line. Record new dependencies in *both* directions: update the plan being depended on too.
- The header carries `**Reviews:**`. It is `None — <reason>` when a test, a build, or a query verifies the change on the day, and one dated bullet per review when only live data over time can judge it (prompt text, thresholds, ranking rules, heuristics, schedules, shares and rates). A plan with reviews has a baseline and predictions table. The rules are in `chalkstream.dev/docs/planning-standards.md` § 2.2.
- Every plan ends with an **Update Documentation** task naming which docs change and how. If none are affected, say so explicitly. A plan without that task is incomplete.
- Tasks are ordered so each one leaves the project working. Each task lists the files it touches and the tests that prove it.
- Cross-repo relative links (`../../backgammondb/docs/…`) are normal and encouraged.
- **Reuse audit:** before proposing new code, search `src/citeio/` and `tests/`. Each task notes what it reuses, or says why it does not.

### Executing a plan

- Work task by task, in order. Update each task's status in the plan file as you go.
- When every task before the deploy is done, set the plan's `Status` to `Built — <when it may deploy>`. The code is then in the tree and not live. A deploy that ships the working tree carries every `Built` plan, so check the `Built` and `In progress` plans before each deploy.
- Documentation tasks are completion criteria, exactly like tests. A plan is not complete while its Update Documentation task is outstanding. Bump the `**Date:**` line on any doc you modify.
- Present the finished work for review. Do not commit.

### The four commands

- `/brainstorm <topic>` — explores a problem in conversation, then writes it up as a spec in `docs/specs/`.
- `/plan <name>` — writes an implementation plan in `docs/plans/`, after scanning for dependencies, reusable code, and affected documentation.
- `/critique <name>` — deep review of a plan, spec, or research doc before executing it. It logs its outcome to the document's **Edit Summary** table and **Edit History** section.
- `/complete-task` — housekeeping once the work is reviewed: moves the plan to `completed/` re-dated to today, cleans up companion files, fixes links, checks documentation, and appends a "Plan complete" entry to the Edit Summary and Edit History. A plan with a review still due moves to `awaiting-review/` instead.
- `/plan-status:plan-status` — a plugin skill installed at user scope, not a file in this repo. It lists every open plan by status and the reviews due; from chalkstream.dev or with the argument `all` it covers the portfolio.

All four live in `.claude/commands/`. Their canonical versions are in
`chalkstream.dev/docs/templates/planning/`.

### Documentation style

- Every doc opens with a title plus a bulleted header list — one bullet each for `**Date:**`, `**Status:**`, `**Scope:**`, and `**Related:**` — and links related docs by relative path. A field with several entries puts each on its own nested bullet.
- Docs explain what **isn't obvious** — decisions, trade-offs, gotchas, blast radius, rejected alternatives — not what a tool's own documentation already covers.
- Don't make assumptions: verify against the actual code, servers, and sibling repos before recording a fact. What gets written down here gets relied on later.
- **Write in Simplified Technical English.** One idea per sentence, active voice, one term per concept, no idioms, and no bare reference labels such as "D6" — name the decision instead. The full rule set is [`../chalkstream.dev/docs/writing-standards.md`](../chalkstream.dev/docs/writing-standards.md).
- **No hard line wrapping in Markdown.** One paragraph, list item, or table row is one line; the editor wraps on screen. Line breaks mark structure only.
