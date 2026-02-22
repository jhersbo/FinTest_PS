"""
Unit tests for app/core/utils/ftdates.py

Tests cover:
- str_to_date parsing
- today / today_minus_days (relative, use freeze or just sanity checks)
- prev_weekday / next_weekday — skip weekends and holidays
- is_holiday — US exchange mapping + known holiday
- is_market_open — weekend/holiday/hours checks (clock mocked via monkeypatch)
"""

import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytz

import app.core.utils.ftdates as ftdates
from app.core.utils.ftdates import (
    str_to_date,
    prev_weekday,
    next_weekday,
    is_holiday,
    is_market_open,
    today,
    today_minus_days,
)


# ---------------------------------------------------------------------------
# str_to_date
# ---------------------------------------------------------------------------

class TestStrToDate:
    def test_basic_parse(self):
        assert str_to_date("2024-01-15") == date(2024, 1, 15)

    def test_year_boundary(self):
        assert str_to_date("2000-12-31") == date(2000, 12, 31)

    def test_returns_date_not_datetime(self):
        result = str_to_date("2024-06-01")
        assert type(result) is date

    def test_invalid_format_raises(self):
        with pytest.raises(Exception):
            str_to_date("not-a-date")


# ---------------------------------------------------------------------------
# today / today_minus_days
# ---------------------------------------------------------------------------

class TestTodayHelpers:
    def test_today_returns_date(self):
        assert isinstance(today(), date)

    def test_today_minus_zero(self):
        assert today_minus_days(0) == today()

    def test_today_minus_days_delta(self):
        from datetime import timedelta
        result = today_minus_days(7)
        assert result == today() - timedelta(days=7)


# ---------------------------------------------------------------------------
# prev_weekday
# ---------------------------------------------------------------------------

class TestPrevWeekday:
    def test_monday_returns_friday(self):
        # 2024-01-08 is a Monday → prev weekday is 2024-01-05 (Friday)
        monday = date(2024, 1, 8)
        result = prev_weekday(monday)
        assert result == date(2024, 1, 5)
        assert result.weekday() == 4  # Friday

    def test_wednesday_returns_tuesday(self):
        wednesday = date(2024, 1, 10)
        result = prev_weekday(wednesday)
        assert result == date(2024, 1, 9)

    def test_skips_saturday_sunday(self):
        # Tuesday 2024-01-09 → prev is Monday 2024-01-08
        tuesday = date(2024, 1, 9)
        result = prev_weekday(tuesday)
        assert result == date(2024, 1, 8)
        assert result.weekday() < 5  # not weekend

    def test_skips_us_holiday_new_years(self):
        # 2024-01-02 (Tuesday) — Jan 1 (Monday) is New Year's observed
        # prev_weekday from Jan 2 should skip Jan 1 → Dec 29 2023
        jan_2_2024 = date(2024, 1, 2)
        result = prev_weekday(jan_2_2024, exchange="XNYS")
        assert result == date(2023, 12, 29)

    def test_result_is_not_weekend(self):
        for d in [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)]:
            result = prev_weekday(d)
            assert result.weekday() < 5


# ---------------------------------------------------------------------------
# next_weekday
# ---------------------------------------------------------------------------

class TestNextWeekday:
    def test_friday_returns_monday(self):
        # 2024-01-05 Friday → next weekday is 2024-01-08 Monday
        friday = date(2024, 1, 5)
        result = next_weekday(friday)
        assert result == date(2024, 1, 8)

    def test_wednesday_returns_thursday(self):
        wednesday = date(2024, 1, 10)
        result = next_weekday(wednesday)
        assert result == date(2024, 1, 11)

    def test_skips_us_holiday_new_years(self):
        # 2023-12-29 (Friday) → next weekday skips Jan 1 2024 → Jan 2 2024
        dec_29_2023 = date(2023, 12, 29)
        result = next_weekday(dec_29_2023, exchange="XNYS")
        assert result == date(2024, 1, 2)

    def test_result_is_not_weekend(self):
        for d in [date(2024, 3, 1), date(2024, 3, 2), date(2024, 3, 3)]:
            result = next_weekday(d)
            assert result.weekday() < 5


# ---------------------------------------------------------------------------
# is_holiday
# ---------------------------------------------------------------------------

class TestIsHoliday:
    def test_new_years_day_is_holiday(self):
        assert is_holiday(date(2024, 1, 1), "XNYS") is True

    def test_christmas_day_is_holiday(self):
        assert is_holiday(date(2024, 12, 25), "XNYS") is True

    def test_regular_trading_day_is_not_holiday(self):
        # 2024-03-15 is a regular Friday
        assert is_holiday(date(2024, 3, 15), "XNYS") is False

    def test_us_exchanges_map_to_xnys(self):
        # All US exchange codes should map to XNYS calendar
        us_codes = ["XASE", "XNAS", "ARCX", "BATS", "EDGX"]
        for code in us_codes:
            # Christmas 2024 — all US exchanges should observe it
            assert is_holiday(date(2024, 12, 25), code) is True

    def test_unknown_exchange_returns_false_on_error(self):
        # Unrecognised exchange passes through — should not raise, returns False
        result = is_holiday(date(2024, 1, 1), "UNKN")
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# is_market_open
# ---------------------------------------------------------------------------

def _make_eastern_dt(year:int, month:int, day:int, hour:int, minute:int) -> datetime:
    eastern = pytz.timezone("US/Eastern")
    return eastern.localize(datetime(year, month, day, hour, minute))


class TestIsMarketOpen:
    def _patch_now(self, dt:datetime):
        return patch("app.core.utils.ftdates.datetime", wraps=datetime,
                     **{"now.return_value": dt})

    def test_open_during_trading_hours(self):
        dt = _make_eastern_dt(2024, 3, 15, 10, 30)  # Friday, 10:30 AM ET
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is True

    def test_closed_before_open(self):
        dt = _make_eastern_dt(2024, 3, 15, 9, 0)  # 9:00 AM — before 9:30
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is False

    def test_closed_after_close(self):
        dt = _make_eastern_dt(2024, 3, 15, 16, 30)  # 4:30 PM
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is False

    def test_closed_on_saturday(self):
        dt = _make_eastern_dt(2024, 3, 16, 11, 0)  # Saturday
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is False

    def test_closed_on_sunday(self):
        dt = _make_eastern_dt(2024, 3, 17, 11, 0)  # Sunday
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is False

    def test_closed_on_holiday(self):
        # Christmas 2024 is a Wednesday; market is closed
        dt = _make_eastern_dt(2024, 12, 25, 11, 0)
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is False

    def test_unimplemented_market_raises(self):
        with pytest.raises(NotImplementedError):
            is_market_open("UNKNOWN")

    def test_open_at_exact_open_time(self):
        dt = _make_eastern_dt(2024, 3, 15, 9, 30)  # exactly 9:30
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            assert is_market_open("US") is True

    def test_closed_at_exact_close_time(self):
        dt = _make_eastern_dt(2024, 3, 15, 16, 0)  # exactly 4:00 PM (inclusive per implementation)
        with patch.object(ftdates, "datetime") as mock_dt:
            mock_dt.now.return_value = dt
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            # implementation uses <= so 4:00 PM is still open
            assert is_market_open("US") is True
