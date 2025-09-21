import datetime
from datetime import date, timedelta

def today() -> date:
    """
    Returns today's date (e.g. yyyy-MM-dd)
    """
    return datetime.date.today()

def today_minus_days(daysBefore: int) -> date:
    """
    Returns the date n days before today
    """
    return today() - timedelta(days=daysBefore)

# TODO - implement a holiday tracker to determine when markets are open/closed

def is_market_open() -> bool:
    return True