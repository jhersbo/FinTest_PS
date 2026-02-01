from datetime import date, timedelta, datetime
import pytz
import holidays

from app.core.utils.logger import get_logger

L = get_logger(__name__)

def today() -> date:
    """
    Returns today's date (e.g. yyyy-MM-dd)
    """
    return date.today()

def today_minus_days(daysBefore: int) -> date:
    """
    Returns the date n days before today
    """
    return today() - timedelta(days=daysBefore)

def str_to_date(date_str:str) -> date:
    """
    Converts a yyyy-MM-dd date string into a date object
    """
    parts = [int(pt) for pt in str(date_str).split("-")]
    return date(year=parts[0], month=parts[1], day=parts[2])

def prev_weekday(date:date, exchange:str="XNYS") -> date:
    """
    Returns the prior non-holiday weekday date
    """
    d = date - timedelta(days=1)
    if d.weekday() > 4 or is_holiday(d, exchange):
        return prev_weekday(d)
    return d

def next_weekday(date:date, exchange:str="XNYS") -> date:
    """
    Returns the next non-holiday weekday date
    """
    d = date + timedelta(days=1)
    if d.weekday() > 4 or is_holiday(d, exchange):
        return next_weekday(d)
    return d

def is_holiday(d:date, exchange:str) -> bool:
    us_ex_tup = (
        "XASE",
        "XBOS",
        "XCIS",
        "FINR",
        "24EQ",
        "MRPL",
        "XISE",
        "EDGA",
        "EDGX",
        "LTSE",
        "XCHI",
        "XNYS",
        "ARCX",
        "XNAS",
        "MEMX",
        "IEXG",
        "CBSX",
        "XPSX",
        "BATY",
        "BATS"
    )
    ex = "XNYS" if exchange in us_ex_tup else exchange
    try:
        h = holidays.financial_holidays(market=ex)
        return d in h
    except:
        L.exception(f"Exception thrown while interpreting holiday: {str(d)} | {exchange}")
    return False

def is_market_open(market:str="US") -> bool:
    """
    Checks to see if the selected market is open
    """
    if market == "US":
        eastern_tz = pytz.timezone("US/Eastern")
        now = datetime.now(eastern_tz)
        # Check if weekend
        if now.weekday() >= 5: 
            return False
        # Check if holiday
        us_holidays = holidays.country_holidays(country="US", subdiv="NY")
        if now.date() in us_holidays:
            return False
        # Market hours: 9:30 AM to 4:00 PM Eastern Time
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return market_open <= now <= market_close
    
    raise NotImplementedError(f"{market} has not been implemented for this function. ")