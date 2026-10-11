import io
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

import citeio
from citeio import APIError, Client


class FakeResponse(io.BytesIO):
    status = 200


class FakeUrlopen:
    """Records each `Request` and answers from a queue of bodies or errors."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.requests = []
        self.timeouts = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, bytes):
            return FakeResponse(answer)
        return FakeResponse(json.dumps(answer).encode())


@pytest.fixture
def fake(monkeypatch):
    def install(*answers):
        f = FakeUrlopen(*answers)
        monkeypatch.setattr("citeio.client.urlopen", f)
        return f

    return install


def query(request):
    return {k: v[0] for k, v in parse_qs(urlparse(request.full_url).query).items()}


def test_request_headers(fake):
    f = fake({"id": "r1"})
    Client("key-1", timeout=7).get_report("r1")
    request = f.requests[0]
    assert request.get_header("X-api-key") == "key-1"
    assert request.get_header("User-agent") == (
        f"citeio-python/{citeio.__version__} (+https://github.com/chalkstreamdev/citeio-python)"
    )
    assert request.get_header("Accept") == "application/json"
    assert f.timeouts == [7]


def test_base_url_normalised(fake):
    for base in ("https://cite.io/api", "https://cite.io/api/"):
        f = fake({"id": "r1"})
        Client("k", base_url=base).get_report("r1")
        assert f.requests[0].full_url == "https://cite.io/api/reports/r1/"


def test_default_base_url(fake):
    f = fake({"id": "r1"})
    Client("k").get_report("r1")
    assert f.requests[0].full_url.startswith("https://cite.io/api/")


def test_list_reports_pages_until_short(fake):
    pages = [[{"id": f"r{n}"} for n in range(start, start + size)]
             for start, size in ((0, 50), (50, 50), (100, 7))]
    f = fake(*pages)
    rows = Client("k").list_reports("P1")
    assert len(rows) == 107
    assert [query(r) for r in f.requests] == [
        {"project_id": "P1", "limit": "50", "offset": str(offset)} for offset in (0, 50, 100)
    ]


def test_list_reports_dedupes_across_pages(fake):
    first = [{"id": f"r{n}"} for n in range(50)]
    second = [{"id": "r49", "late": True}, {"id": "r50"}]
    fake(first, second)
    rows = Client("k").list_reports("P1")
    assert [r["id"] for r in rows] == [f"r{n}" for n in range(51)]
    assert "late" not in rows[49]


def test_get_report(fake):
    f = fake({"id": "r1", "presentation": {"title": "T"}})
    assert Client("k").get_report("r1") == {"id": "r1", "presentation": {"title": "T"}}
    assert f.requests[0].full_url == "https://cite.io/api/reports/r1/"


def test_non_2xx_raises_apierror(fake):
    url = "https://cite.io/api/reports/nope/"
    fake(HTTPError(url, 404, "Not Found", {}, io.BytesIO(b'{"detail": "Not found."}')))
    with pytest.raises(APIError) as caught:
        Client("k").get_report("nope")
    assert caught.value.status == 404
    assert caught.value.url == url
    assert caught.value.body == '{"detail": "Not found."}'
    assert APIError.__mro__[1:] == (Exception, BaseException, object)


def test_download_image_streams_without_key(fake, tmp_path):
    f = fake(b"\x89PNG image bytes")
    dest = tmp_path / "card.png"
    Client("secret").download_image("https://cite.io/media/example.png", dest)
    assert dest.read_bytes() == b"\x89PNG image bytes"
    request = f.requests[0]
    assert request.full_url == "https://cite.io/media/example.png"
    assert request.get_header("X-api-key") is None
    assert request.get_header("User-agent").startswith("citeio-python/")
