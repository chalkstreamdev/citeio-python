"""citeio: render Cite research reports on your own site.

The package wraps the five Cite API calls a site needs and turns a report's
or a profile's `presentation` object into two HTML fragments. It has no
dependencies outside the standard library, and it ignores any field it does
not know, so a Cite addition never breaks a page.
"""

__version__ = "0.2.0"

from citeio.client import APIError, Client
from citeio.helpers import parse_datetime, publishable
from citeio.render import body_html, sources_html

__all__ = [
    "APIError",
    "Client",
    "body_html",
    "parse_datetime",
    "publishable",
    "sources_html",
]
