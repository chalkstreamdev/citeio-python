"""Two small helpers every site that publishes Cite reports needs.

`publishable` applies a grade threshold to a report row, and `parse_datetime`
reads the API's timestamps. Neither decides anything Cite has not already
served; they exist so each customer does not re-derive the same two rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any


def publishable(
    row: Mapping[str, Any], min_grade: int = 2, include_ungraded: bool = False
) -> bool:
    """Return True when the report row's `grade` is at least `min_grade`.

    A null or missing `grade` means the report is ungraded, not bad: its
    template has no grading. Such a row is publishable only when
    `include_ungraded` is True. A grade that is not a number is never
    publishable.
    """
    grade = row.get("grade")
    if grade is None:
        return include_ungraded
    if isinstance(grade, bool) or not isinstance(grade, int | float):
        return False
    return grade >= min_grade


def parse_datetime(value: str) -> datetime:
    """Return the aware UTC datetime for an ISO 8601 string from the API.

    A naive value is taken as UTC. A value with another offset is converted
    to UTC, so a date shown on a page or used in a URL is the UTC date.
    """
    parsed = datetime.fromisoformat(value)
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
