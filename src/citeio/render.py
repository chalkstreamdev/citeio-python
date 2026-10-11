"""Turn a report's `presentation` object into two HTML fragments.

`body_html` renders the paragraphs, with external citations as links and
internal citations as links to the caller's own URLs. `sources_html` renders
the Sources list. Cite has already decided every link and every label; this
module only escapes text and writes markup with stable `citeio-` class names.

It ships no CSS and decides nothing about the page around the fragments. It
never raises on Cite's output: a key it does not know is ignored, and a run it
does not understand renders as plain text or as nothing.
"""

from __future__ import annotations

import html
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlparse

Resolve = Callable[[str], Any]

_REL = "noopener noreferrer"


def _presentation(obj: Any) -> Mapping[str, Any]:
    """The presentation object inside `obj`: its `presentation` value when
    `obj` is a report detail, else `obj` itself; `{}` for anything else."""
    if isinstance(obj, Mapping):
        if "presentation" in obj:
            inner = obj["presentation"]
            return inner if isinstance(inner, Mapping) else {}
        return obj
    return {}


def _text(value: str) -> str:
    """Escaped text, with a single newline written as `<br>`."""
    return html.escape(value, quote=True).replace("\n", "<br>")


def _attr(value: str) -> str:
    """An escaped attribute value."""
    return html.escape(value, quote=True)


def _is_web_url(value: Any) -> bool:
    """True when `value` is a string that starts with `http://` or `https://`."""
    return isinstance(value, str) and value.lower().startswith(("http://", "https://"))


def _resolved(resolve: Resolve | None, report_id: str) -> str | None:
    """The caller's URL for `report_id`, or None when there is no resolver or
    it does not return a non-empty string."""
    href = resolve(report_id) if resolve else None
    return href if isinstance(href, str) and href else None


def _rel(nofollow: bool) -> str:
    """The `rel` value for an external link."""
    return f"{_REL} nofollow" if nofollow else _REL


def _external_link(href: str, label: str, nofollow: bool) -> str:
    """An `<a>` for an external URL."""
    return (
        f'<a class="citeio-link citeio-external" href="{_attr(href)}" '
        f'rel="{_rel(nofollow)}">{_text(label)}</a>'
    )


def _internal_link(href: str, label: str) -> str:
    """An `<a>` for a report on the caller's own site; it has no `rel`."""
    return f'<a class="citeio-link citeio-internal" href="{_attr(href)}">{_text(label)}</a>'


def _run(run: Any, resolve: Resolve | None, nofollow: bool) -> str:
    """The markup of one run. A run that is not a dict or has no string
    `text` renders nothing. A run with a string `report_id` is internal, else
    one with a string `url` is external; a link that cannot be made renders
    the text alone."""
    if not isinstance(run, Mapping):
        return ""
    text = run.get("text")
    if not isinstance(text, str):
        return ""
    report_id, url = run.get("report_id"), run.get("url")
    if isinstance(report_id, str):
        href = _resolved(resolve, report_id)
        return _internal_link(href, text) if href else _text(text)
    if isinstance(url, str):
        return _external_link(url, text, nofollow) if _is_web_url(url) else _text(text)
    return _text(text)


def body_html(
    report_or_presentation: Any,
    resolve: Resolve | None = None,
    *,
    nofollow: bool = False,
) -> str:
    """Return the report's paragraphs as `<p class="citeio-paragraph">`
    elements joined by newlines, or `""` when there are none.

    `report_or_presentation` is the report detail from `Client.get_report` or
    its `presentation` object. `resolve` maps a report id to a URL on your
    site, or to None; an internal run whose id does not resolve renders as
    plain text. External links carry `rel="noopener noreferrer"`, plus
    `nofollow` when asked. Only `http` and `https` URLs become links.
    """
    paragraphs = _presentation(report_or_presentation).get("paragraphs")
    if not isinstance(paragraphs, list):
        return ""
    return "\n".join(
        '<p class="citeio-paragraph">'
        + "".join(_run(run, resolve, nofollow) for run in paragraph)
        + "</p>"
        for paragraph in paragraphs
        if isinstance(paragraph, list)
    )


def _host(url: str) -> str:
    """The host of `url` without a leading `www.`, as Cite labels a source."""
    host = urlparse(url).netloc or url
    return host[4:] if host.startswith("www.") else host


def _source(source: Any, resolve: Resolve | None, nofollow: bool) -> str:
    """The `<li>` of one source, or `""` when it cannot be linked."""
    if not isinstance(source, Mapping):
        return ""
    label = source.get("label")
    if not (isinstance(label, str) and label):
        label = None
    report_id, url = source.get("report_id"), source.get("url")
    if isinstance(report_id, str):
        href = _resolved(resolve, report_id)
        if not href:
            return ""
        kind = "citeio-internal"
        link = _internal_link(href, label or report_id)
    elif _is_web_url(url):
        kind = "citeio-external"
        link = _external_link(url, label or _host(url), nofollow)
    else:
        return ""
    primary = " citeio-primary" if source.get("primary") else ""
    return f'<li class="citeio-source {kind}{primary}">{link}</li>'


def sources_html(
    report_or_presentation: Any,
    resolve: Resolve | None = None,
    *,
    nofollow: bool = False,
) -> str:
    """Return the Sources list as a `<ul class="citeio-sources">`, or `""`
    when no source can be linked.

    Takes the same arguments as `body_html`. The order is Cite's: primary
    sources first. An internal source whose id does not resolve is left out,
    and an internal source's link text is the target report's title.
    """
    sources = _presentation(report_or_presentation).get("sources")
    if not isinstance(sources, list):
        return ""
    items = [li for li in (_source(s, resolve, nofollow) for s in sources) if li]
    if not items:
        return ""
    return '<ul class="citeio-sources">\n' + "\n".join(items) + "\n</ul>"
