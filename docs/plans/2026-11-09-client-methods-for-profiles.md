# Implementation Plan: Client methods for profiles

- **Date:** 2026-11-09
- **Status:** Built — 2026-11-10, every step but the tag is done and 40 tests pass. Nick commits and tags `v0.2.0` (Task 3 Step 3); the two Cite doc rows then change from Built to Done
- **Scope:** Two `Client` methods for Cite's profile endpoints, a profile fixture that proves `body_html` and `sources_html` render a profile unchanged, and the `v0.2.0` release. It adds no public name and no rendering rule: a profile's `presentation` has the report's shape. The newsroom generator's use of the methods is a newsroom plan.
- **Depends on:**
  - [`../../../cite/docs/plans/2026-11-01-profile-report.md`](../../../cite/docs/plans/2026-11-01-profile-report.md) — Task 11 built the two endpoints, live since `4cdf1b1` on 2026-11-05; Task 15 created this plan
- **Blocks:**
  - [`../../../newsroom/docs/plans/2026-11-09-entity-profile-step.md`](../../../newsroom/docs/plans/2026-11-09-entity-profile-step.md) — the generator's profile step calls these methods and pins `v0.2.0`
- **Reviews:** None — the tests and one live call verify the change on the day
- **Related:**
  - [`../../../newsroom/docs/specs/2026-10-23-entity-profile-content.md`](../../../newsroom/docs/specs/2026-10-23-entity-profile-content.md) — § 3.6, step 3: "one client method for profiles, and a new tag"
  - [`../../../cite/docs/specs/2026-10-30-profile-report.md`](../../../cite/docs/specs/2026-10-30-profile-report.md) — the profile report: what a version is, and why it never changes
  - [`../../../cite/docs/api/presentation.md`](../../../cite/docs/api/presentation.md) — the shape a profile version's `presentation` shares with a report's
  - [`../../../chalkstream.dev/docs/specs/2026-09-23-citeio-python-library.md`](../../../chalkstream.dev/docs/specs/2026-09-23-citeio-python-library.md) — the library's design: the standard library only, Cite decides and the library renders, nothing breaks on a new field

## Edit Summary

| Date | Changes | Summary |
|------|---------|---------|
| 2026-11-09 | 2 fixes, 0 skips | Critique: the fixture is saved as served (`Invoke-WebRequest -OutFile`), not parsed and rewritten; the render tests pass the whole detail, as a site does |
| 2026-11-09 | Plan created | Four tasks: two client methods, a profile fixture with render tests, the `v0.2.0` release, and documentation. Written by the Cite profile plan's consumer plans task |

Cite writes a profile of each entity of a project: one value of one choice field, such as the operator "Kalshi", once that value has five reports. Each rewrite is a new version with its own public id, and a version never changes after it is written. Cite serves profiles through two endpoints, which stay out of `GET /api/reports/`, so no consumer of the report endpoints sees a profile:

- `GET /api/projects/{project_id}/profiles/?field=<key>` — one item per value on the field's choice list that has at least one version, in the list's order: `{"value": ..., "versions": [{"id", "created_at", "grade"}, ...]}`, with the versions newest first. It is not paginated. It returns 404 when the project is not the key's organisation's, or when `field` is not a choice field of the project's template.
- `GET /api/profiles/{version_id}/` — `id`, `project` (`{"id", "name"}`), `field`, `value`, `created_at`, `grade`, `grade_detail` (null when ungraded), `content` and `presentation`. `content` holds the four keys every profile template starts with (`title`, `subtitle`, `body`, `citations`) and the template's data fields, each null when no source supports a value. `presentation` has the report's shape, and its internal links are report ids, never URLs.

The library needs one method per endpoint. A version's `presentation` already renders through `body_html` and `sources_html`, and a version row's `grade` already works with `publishable`, so neither changes. The Cite plan named the methods `profiles` and `profile`. This plan names them `list_profiles` and `get_profile`, after the library's own `list_reports` and `get_report`.

**Tech Stack:** Python 3.11+ standard library (`urllib`, `json`), pytest, ruff.

**Reuse:** both methods are one call to `Client._get_json`, which already sends the key, the User-Agent and the timeout, and raises `APIError` on a non-2xx response. The tests reuse `FakeUrlopen` and `query` from `tests/test_client.py`. Nothing new is needed in `render.py` or `helpers.py`.

---

## Task 1: `list_profiles` and `get_profile`

**Status:** Done 2026-11-10 — both methods and the five tests are in; 36 tests pass and ruff passes. Cite's `research/views.py` confirms both paths and both shapes

**Files:**
- Modify: `src/citeio/client.py` (the two methods; the module docstring's "three calls" becomes five)
- Modify: `src/citeio/__init__.py` (the module docstring's "three Cite API calls")
- Modify: `tests/test_client.py`

**Step 1: The list.** `list_profiles(self, project_id: str, field: str) -> list[dict[str, Any]]` returns `self._get_json(f"projects/{project_id}/profiles/", field=field)`, as served. Its docstring says: one item per value with a version, in the choice list's order; each item's versions are newest first, each with `id`, `created_at` and `grade` (1 to 3, or null for ungraded); the list is one call, not paged; a version never changes, so a caller fetches each `id` once and keeps it.

**Step 2: The detail.** `get_profile(self, version_id: str) -> dict[str, Any]` returns `self._get_json(f"profiles/{version_id}/")`. Its docstring says: the version's `content` and `presentation`, with the list fields; `presentation` renders with `body_html` and `sources_html` as a report's does; internal links are report ids, resolved by the caller.

**Tests:**
- `test_list_profiles_path_and_field`: one request to `projects/p1/profiles/` with `field=operator` in the query, and the body returned as served.
- `test_list_profiles_is_one_call`: a list of 60 items makes one request (the report list pages at 50; this one does not).
- `test_get_profile_path`: one request to `profiles/v1/`.
- `test_profile_calls_send_the_headers`: the key, the User-Agent and the timeout, as `test_request_headers` checks for `get_report`.
- `test_profile_404_raises_api_error`: a 404 raises `APIError` with `status` 404 and the URL.

**Success criteria:** `uv run pytest -q` and `uv run ruff check .` pass.

---

## Task 2: A profile fixture, and the render tests

**Status:** Done 2026-11-10 — Nick saved Kalshi's version `d53FqAx8xN` as served (graded 3; 4 paragraphs, 9 internal and 3 external runs, 12 sources). It holds no key and no image URL; its only URLs are on kalshi.com, help.kalshi.com and en.wikipedia.org. 40 tests pass, and `presentation.html` does not change

**Files:**
- Create: `tests/fixtures/profile_detail.json`
- Modify: `tests/test_render.py`, `tests/test_helpers.py`

**Step 1: The fixture.** One profile version's detail from Predictable, Chalkstream's own project, so the public repository holds no customer's text, no key and no image URL (a profile has no image). The version is Kalshi's `d53FqAx8xN`, written on 2026-11-06 and graded green. Nick fetches it once with his key, as he did for the report fixture:

```powershell
$key = Read-Host -AsSecureString "Cite API key"
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($key))
Invoke-WebRequest -Uri "https://cite.io/api/profiles/d53FqAx8xN/" -Headers @{ "X-API-Key" = $plain } -OutFile tests\fixtures\profile_detail.json
```

`-OutFile` saves the response's bytes as served, so the fixture is the response verbatim. `Invoke-RestMethod` piped to `ConvertTo-Json` would not be: it parses the JSON into objects, turns ISO timestamps into `DateTime` values, and writes new JSON. If that version is gone, any green Predictable version from the list serves.

**Step 2: Render it.** Render the fixture, the whole detail, with `body_html(detail, resolve)` and `sources_html(detail, resolve)`, as a site calls them for a report (the newsroom generator's `present` does so). Both functions find the `presentation` inside a detail.

**Tests:**
- `test_profile_detail_renders`: given the whole detail, `body_html` returns one `<p>` per paragraph and `sources_html` one `<li>` per source, with no error, and the same HTML as given the detail's `presentation`.
- `test_profile_internal_links_use_the_resolver`: an internal citation renders as a link when the resolver returns a URL, and as plain text when it returns `None`.
- `test_profile_unknown_keys_are_ignored`: a copy of the fixture with an extra top-level key and an extra run key renders the same HTML.
- `test_publishable_reads_a_version_row` (in `tests/test_helpers.py`): `publishable` accepts a list item's version, `{"id", "created_at", "grade"}`, by the same grade rule, and a null grade is not publishable.

**Success criteria:** the suite passes; `tests/fixtures/presentation.html` does not change, because no markup changes.

---

## Task 3: Release `v0.2.0`

**Status:** In progress — Steps 1 and 2 done 2026-11-10. The changelog section is dated 2026-11-10; change the date if the tag lands on a later day. Step 3, the tag, is Nick's

**Files:**
- Modify: `src/citeio/__init__.py` (`__version__ = "0.2.0"`)
- Modify: `CHANGELOG.md`

**Step 1: The version.** Two new methods and no change to an existing one is a minor release under Semantic Versioning, so the version becomes `0.2.0`.

**Step 2: The changelog.** A `[0.2.0]` section dated on release day, under "Added": `Client.list_profiles` and `Client.get_profile`, the profile endpoints of Cite; one line that a profile's `presentation` renders with `body_html` and `sources_html` unchanged. The compare links at the foot gain `v0.2.0`.

**Step 3: The tag.** Nick tags `v0.2.0` and pushes the tag. The newsroom plan pins it.

**Tests:** the suite and ruff pass on the release commit.

**Success criteria:** the `v0.2.0` tag exists on GitHub, and `citeio.__version__` is `"0.2.0"` at that tag.

---

## Task 4: Update Documentation

**Status:** In progress — every doc below updated 2026-11-10. The two Cite docs mark the citeio work Built, because the tag does not exist yet. At the tag, both rows change to Done and `consumers.md`'s citeio row drops "not yet tagged"

- `README.md` — a "Profiles" section after "Internal links": the two methods, in four or five lines of code that list a field's profiles, choose the newest publishable version and render it; one line that a version never changes, so a site caches it by id.
- `CLAUDE.md` — "wraps the three Cite API calls a site needs" becomes five calls: the report list, one report, one profile list, one profile version and an image download. The public API stays six names.
- `../chalkstream.dev/docs/specs/2026-09-23-citeio-python-library.md` — the step list of § 3.5 gains a line for this release; bump the `**Date:**` line.
- `../cite/docs/api/consumers.md` — the citeio row's "Reads" gains the two profile endpoints, and § Open consumer work marks this plan done. Bump the `**Date:**` line.
- `../cite/docs/api/profiles.md` — the § Consumers row for `citeio` marks this plan done, with the `v0.2.0` tag. Bump the `**Date:**` line. Added 2026-11-10: Cite's change note appeared after this plan was written.
- Done beyond the list above: the library spec's § 3.3 client paragraph named "three GET calls" and said the client covers reading reports only. It now names five calls and the two profile methods, and its Edit Summary has a row for the change.

---

## Edit History

### 2026-11-09 — Critique

**Fixes:**
- **[moderate] The fixture command rewrote the response** — `Invoke-RestMethod` piped to `ConvertTo-Json` parses the JSON and writes new JSON, and PowerShell 7 turns ISO timestamps into `DateTime` values on the way, so the fixture would not have been the response verbatim. Task 2 Step 1 now saves the bytes with `Invoke-WebRequest -OutFile`.
- **[minor] The render tests passed only the `presentation`** — A site passes the whole detail to `body_html` and `sources_html`. Task 2 now renders the detail and checks that it gives the same HTML as its `presentation`.
