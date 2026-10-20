import html
import json
import re
from pathlib import Path

import pytest

from citeio import body_html, sources_html

FIXTURES = Path(__file__).parent / "fixtures"
resolve = {"rA1green": "/news/rA1green/polymarket-record/"}.get


@pytest.fixture
def p():
    return json.loads((FIXTURES / "presentation.json").read_text(encoding="utf-8"))


def test_paragraphs_become_p_elements():
    out = body_html({"paragraphs": [[{"text": "One."}], [{"text": "Two."}]]})
    assert out == '<p class="citeio-paragraph">One.</p>\n<p class="citeio-paragraph">Two.</p>'


def test_external_run_is_a_link_with_rel(p):
    assert (
        '<a class="citeio-link citeio-external" href="https://www.polymarket.com/stats" '
        'rel="noopener noreferrer">exchange&#x27;s own dashboard</a>'
    ) in body_html(p, resolve)


def test_nofollow_adds_to_rel(p):
    out = body_html(p, resolve, nofollow=True)
    assert 'rel="noopener noreferrer nofollow">exchange&#x27;s own dashboard</a>' in out
    assert '<a class="citeio-link citeio-internal" href="/news/rA1green/polymarket-record/">' in out
    assert out.count("rel=") == 1


def test_internal_run_uses_the_resolver(p):
    assert (
        '<a class="citeio-link citeio-internal" href="/news/rA1green/polymarket-record/">'
        "reported last week</a>"
    ) in body_html(p, resolve)


def test_internal_run_unresolved_is_plain_text(p):
    for out in (body_html(p, lambda report_id: None), body_html(p)):
        assert "As we reported last week, volume set a record." in out
        assert "citeio-internal" not in out


def test_resolver_result_that_is_not_a_string_is_plain_text():
    p = {"paragraphs": [[{"text": "x", "report_id": "r1"}]]}
    for value in ("", Path("/news/r1/"), 3):
        assert body_html(p, lambda report_id, v=value: v) == '<p class="citeio-paragraph">x</p>'


def test_text_is_escaped(p):
    out = body_html(p, resolve)
    assert "3 &lt; 5 &amp; &quot;quoted&quot;." in out
    assert "exchange&#x27;s" in out
    link = body_html({"paragraphs": [[{"text": "a", "url": "https://x.example/?a=1&b=2"}]]})
    assert 'href="https://x.example/?a=1&amp;b=2"' in link


def test_single_newline_is_br(p):
    assert '<p class="citeio-paragraph">Line one<br>line two and a ' in body_html(p, resolve)


def test_non_http_url_is_plain_text(p):
    out = body_html(p, resolve)
    assert "and a bad link." in out
    assert "javascript:" not in out
    upper = body_html({"paragraphs": [[{"text": "a", "url": "HTTPS://x.example/"}]]})
    assert 'href="HTTPS://x.example/"' in upper


def test_unknown_run_keys_are_ignored():
    assert body_html({"paragraphs": [[{"text": "x", "footnote": 3}]]}) == (
        '<p class="citeio-paragraph">x</p>'
    )
    assert body_html({"paragraphs": [[{"note": "y"}, {"text": 5}, "z"]]}) == (
        '<p class="citeio-paragraph"></p>'
    )
    assert body_html({"paragraphs": ["not a list", [{"text": "x"}]]}) == (
        '<p class="citeio-paragraph">x</p>'
    )
    assert body_html({"paragraphs": "nope"}) == ""
    assert body_html(None) == ""
    assert body_html({}) == ""
    assert body_html({"presentation": None}) == ""


def test_accepts_the_report_detail(p):
    assert body_html({"id": "r1", "presentation": p}, resolve) == body_html(p, resolve)
    assert sources_html({"id": "r1", "presentation": p}, resolve) == sources_html(p, resolve)


def test_sources_list(p):
    lines = sources_html(p, resolve).split("\n")
    assert lines == [
        '<ul class="citeio-sources">',
        '<li class="citeio-source citeio-external citeio-primary">'
        '<a class="citeio-link citeio-external" href="https://www.polymarket.com/stats" '
        'rel="noopener noreferrer">polymarket.com</a></li>',
        '<li class="citeio-source citeio-external">'
        '<a class="citeio-link citeio-external" href="https://example.com/data?a=1&amp;b=2" '
        'rel="noopener noreferrer">example.com</a></li>',
        '<li class="citeio-source citeio-internal">'
        '<a class="citeio-link citeio-internal" href="/news/rA1green/polymarket-record/">'
        "Polymarket volume doubles</a></li>",
        "</ul>",
    ]


def test_sources_label_falls_back():
    out = sources_html(
        {"sources": [{"url": "https://www.a.example/x"}, {"report_id": "r1"}]},
        {"r1": "/r1/"}.get,
    )
    assert ">a.example</a>" in out
    assert ">r1</a>" in out


def test_sources_empty_is_empty_string(p):
    assert sources_html({"sources": []}) == ""
    assert sources_html({}) == ""
    assert sources_html({"sources": [{"report_id": "rA1green"}]}) == ""
    assert sources_html({"sources": [{"url": "ftp://x.example/", "label": "x"}]}) == ""


def test_golden_file(p):
    expected = (FIXTURES / "presentation.html").read_text(encoding="utf-8")
    assert body_html(p, resolve) + "\n" + sources_html(p, resolve) == expected


# The live fixture is one Predictable report detail captured from cite.io on
# 2026-10-20 (plan Task 6), with both image URLs replaced by placeholders.
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)*")


@pytest.fixture
def live():
    return json.loads((FIXTURES / "report_detail.json").read_text(encoding="utf-8"))


def test_live_fixture_runs_join_to_paragraphs(live):
    body = live["content"]["body"].replace("\r\n", "\n").replace("\r", "\n").strip()
    expected = [t.strip() for t in _PARAGRAPH_BREAK.split(body) if t.strip()]
    served = ["".join(r["text"] for r in para) for para in live["presentation"]["paragraphs"]]
    assert served == expected
    assert expected, "the fixture has a body"


def test_live_fixture_renders(live):
    runs = [r for para in live["presentation"]["paragraphs"] for r in para]
    external = [r for r in runs if "url" in r]
    internal = [r for r in runs if "report_id" in r]
    assert external and internal, "the fixture has both citation kinds"
    out = body_html(live)
    assert out.count('<a class="citeio-link citeio-external"') == len(external)
    assert "citeio-internal" not in out
    assert out.count('<p class="citeio-paragraph">') == len(live["presentation"]["paragraphs"])
    for run in internal:
        assert html.escape(run["text"], quote=True) in out
