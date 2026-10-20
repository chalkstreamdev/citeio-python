# citeio

[Cite](https://cite.io) writes research reports and serves them through an API. `citeio` puts those reports on your own site. It wraps the API calls a site needs, and it turns a report into two HTML fragments: the body, with citations as links, and the Sources list. Cite decides which text is the title, where each link goes, and what each report's URL slug is. Your site decides only the page around the fragments.

## Install

```bash
uv add git+https://github.com/chalkstreamdev/citeio-python
```

or

```bash
pip install git+https://github.com/chalkstreamdev/citeio-python
```

## Ten lines

```python
import citeio

client = citeio.Client(api_key="...")
rows = [r for r in client.list_reports(project_id="...") if citeio.publishable(r)]
slugs = {r["id"]: r["slug"] for r in rows}
report = client.get_report(rows[0]["id"])

def resolve(report_id):          # your URL for a report you published, or None
    return f"/news/{slugs[report_id]}/" if report_id in slugs else None

print(citeio.body_html(report, resolve))
print(citeio.sources_html(report, resolve))
```

The API key comes from your Cite organisation. Keep it out of your code: read it from the environment.

## Internal links

A report can cite an earlier report from the same organisation. Cite sends that citation as a report id, not as a URL, because Cite does not know your URL scheme or which reports you published.

`resolve` is a function that you supply. It takes a report id and returns your URL for that report, or `None`. When it returns `None`, the citation renders as plain text and the report is left out of the Sources list. When you omit `resolve`, every internal citation renders as plain text.

## The `presentation` object

`get_report` returns the report detail. Its `presentation` key holds the parts of the report that a page shows: `title`, `short_title`, `subtitle`, `paragraphs`, and `sources`. Each paragraph is a list of runs. A run is plain text, an external link (`url`), or an internal link (`report_id`). Cite computes the object from the stored report on every request. The full field list is in the [API reference](https://cite.io/api/docs).

`body_html` and `sources_html` accept the report detail or the `presentation` object. Both escape all text. Only `http` and `https` URLs become links. External links carry `rel="noopener noreferrer"`; pass `nofollow=True` to add `nofollow`. A field or a run that the library does not know renders as plain text or as nothing, so a new Cite field does not break your page.

The markup carries class names and no CSS:

| Element | Classes |
|---|---|
| `<p>` | `citeio-paragraph` |
| `<a>` | `citeio-link`, plus `citeio-external` or `citeio-internal` |
| `<ul>` | `citeio-sources` |
| `<li>` | `citeio-source`, plus `citeio-external` or `citeio-internal`, plus `citeio-primary` for a primary source |

## Post URLs

Build each report's URL from the `slug` on its list row. Cite sets the slug once, when it writes the report. The slug is unique within the project and never changes. Do not make a slug from a title: two reports can have the same title, and a title-made slug can differ from Cite's.

## Helpers

- `citeio.publishable(row, min_grade=2, include_ungraded=False)` is True when the row's `grade` is at least `min_grade`. A null grade means the report is ungraded, not bad: its template has no grading. Pass `include_ungraded=True` to publish ungraded reports.
- `citeio.parse_datetime(value)` reads a timestamp from the API, such as `created_at`, and returns an aware UTC `datetime`.

## Errors

A non-2xx response raises `citeio.APIError`, with `status`, `url`, and `body` (the first 500 characters of the response). Network errors and timeouts pass through unchanged. The client does not retry and does not cache: run your build on a schedule, and the next run is the retry.

## Requirements

Python 3.11 or later. No dependencies outside the standard library.

## Licence

MIT. See [LICENSE](LICENSE).
