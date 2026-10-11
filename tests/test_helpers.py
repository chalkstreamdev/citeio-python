from datetime import UTC, datetime

from citeio import parse_datetime, publishable


def test_publishable_default_rule():
    assert publishable({"grade": 3})
    assert publishable({"grade": 2})
    assert not publishable({"grade": 1})
    assert not publishable({"grade": None})
    assert not publishable({})


def test_publishable_include_ungraded():
    assert publishable({"grade": None}, include_ungraded=True)
    assert publishable({}, include_ungraded=True)
    assert not publishable({"grade": 1}, include_ungraded=True)


def test_publishable_min_grade():
    assert publishable({"grade": 3}, min_grade=3)
    assert not publishable({"grade": 2}, min_grade=3)


def test_publishable_grade_that_is_not_a_number():
    assert not publishable({"grade": "3"})
    assert not publishable({"grade": True})


def test_parse_datetime_forms():
    expected = datetime(2026, 9, 15, 7, 0, tzinfo=UTC)
    for value in ("2026-09-15T07:00:00Z", "2026-09-15T07:00:00+00:00", "2026-09-15T07:00:00"):
        parsed = parse_datetime(value)
        assert parsed == expected
        assert parsed.utcoffset() == expected.utcoffset()


def test_parse_datetime_converts_other_offsets_to_utc():
    assert parse_datetime("2026-09-15T08:00:00+01:00").isoformat() == "2026-09-15T07:00:00+00:00"
    assert parse_datetime("2026-09-16T23:30:00-02:00").isoformat() == "2026-09-17T01:30:00+00:00"
