from datetime import datetime

from beaverhabits.utils import format_date_difference


def s2d(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def test_date_diff_format():
    start = "2025-05-28"

    # diff >= 1y
    assert format_date_difference(s2d(start), s2d("2026-05-28")) == "1y"
    # diff >= 1m
    assert format_date_difference(s2d(start), s2d("2025-06-28")) == "1m"
    assert format_date_difference(s2d(start), s2d("2025-06-29")) == "1m1d"
    # diff >= 1w
    assert format_date_difference(s2d(start), s2d("2025-06-03")) == "1w"
    assert format_date_difference(s2d(start), s2d("2025-06-05")) == "1w2d"
    # diff < 1w
    assert format_date_difference(s2d(start), s2d("2025-05-28")) == ""
    assert format_date_difference(s2d(start), s2d("2025-05-29")) == "2d"

    assert format_date_difference(s2d(start), s2d("2025-05-27")) == ""
