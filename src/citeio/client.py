"""The HTTP client for Cite's public API, on the standard library.

Three calls, all a site needs: the report list for one project, one report's
detail, and an image download. There are no retries and no caching: the
customer's scheduler is the retry, and the customer's build owns any cache.
Network errors (`URLError`, timeouts) pass through unchanged, because they are
not the API's fault. A non-2xx response raises `APIError`.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from citeio import __version__

PAGE_SIZE = 50  # the API caps `limit` at 50
DEFAULT_BASE_URL = "https://cite.io/api/"
DEFAULT_USER_AGENT = f"citeio-python/{__version__} (+https://github.com/chalkstreamdev/citeio-python)"


class APIError(Exception):
    """A non-2xx response from Cite. Carries `status`, `url`, and `body`,
    the first 500 characters of the response body."""

    def __init__(self, status: int, url: str, body: str) -> None:
        super().__init__(f"Cite API returned {status} for {url}: {body}")
        self.status = status
        self.url = url
        self.body = body


class Client:
    """A Cite API client that sends the organisation's `X-API-Key`, a
    User-Agent, and a fixed timeout on every request."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        user_agent: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.user_agent = user_agent or DEFAULT_USER_AGENT

    def _open(self, url: str, headers: dict[str, str]) -> Any:
        """The open response for `url`; an `HTTPError` becomes `APIError`."""
        try:
            return urlopen(Request(url, headers=headers), timeout=self.timeout)
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")[:500]
            raise APIError(error.code, url, body) from error

    def _get_json(self, path: str, **params: Any) -> Any:
        """The decoded JSON of `GET base_url + path` with `params` as the query."""
        url = self.base_url + path
        if params:
            url += "?" + urlencode(params)
        headers = {
            "X-API-Key": self.api_key,
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        with self._open(url, headers) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_reports(self, project_id: str) -> list[dict[str, Any]]:
        """Return every report row of `project_id`, newest first.

        Pages through the list 50 rows at a time until a page comes back
        short. A report that arrives while the pages are fetched can push a
        row onto the next page; each `id` is kept once, at its first
        position. Rows carry no content; `get_report` has it.
        """
        rows: list[dict[str, Any]] = []
        seen: set[Any] = set()
        offset = 0
        while True:
            page = self._get_json(
                "reports/", project_id=project_id, limit=PAGE_SIZE, offset=offset
            )
            for row in page:
                if row.get("id") not in seen:
                    seen.add(row.get("id"))
                    rows.append(row)
            if len(page) < PAGE_SIZE:
                return rows
            offset += PAGE_SIZE

    def get_report(self, report_id: str) -> dict[str, Any]:
        """Return the detail of one report: its `content`, its `presentation`
        object, and the same fields as its list row."""
        return self._get_json(f"reports/{report_id}/")

    def download_image(self, url: str, dest: str | os.PathLike[str]) -> None:
        """Stream the image at `url` to `dest`. Returns nothing.

        The image URL is itself the credential, so no API key is sent. The
        file is written in place; rename it into position afterwards if you
        need the write to be atomic.
        """
        with self._open(url, {"User-Agent": self.user_agent}) as response, open(dest, "wb") as f:
            shutil.copyfileobj(response, f, 65536)
