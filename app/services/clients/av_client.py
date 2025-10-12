from dotenv import get_key
from requests import get
from typing import Optional

import pandas as pd

from ...core.utils.logger import get_logger
from .client_utils import ratelimit

L = get_logger(__name__)

class AVClient():
    """
    Client class to access the Alpha Vantage API
    """

    QUERY_URL_BASE = "https://www.alphavantage.co/query?"

    def __init__(self):
        self.KEY = get_key(".env", "ALPHA_VANTAGE_API_KEY")
        if self.KEY is None:
            raise RuntimeError("No API key found for " + __name__)
   
    ################
    # CLIENT METHODS
    ################
    @ratelimit()
    async def time_series_daily(self, symbol=None, adjusted:bool=False, full=False) -> Optional[pd.DataFrame]:
        if symbol is None:
            raise ValueError("A symbol must be provided")
        query = {
            "function": f"TIME_SERIES_DAILY{'_ADJUSTED' if adjusted else ''}",
            "symbol": symbol,
            "outputsize": f"{'full' if full else 'compact'}"
        }
        url = self.__build_url__(query)
        json = get(url=url).json()
        df = pd.DataFrame.from_dict(json["Time Series (Daily)"], orient="index")
        df = df.sort_index(ascending=False).reset_index().rename(columns={"index": "date"})
        df.columns = df.columns.str.replace(pat=r"^\d+\.\s*", repl="", regex=True)
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

        return df

    ##############
    # UTIL METHODS
    ##############
    def __append_key__(self, url:str) -> str:
        """
        Appends the api key to a passed url string
        """
        if url.find("?") == -1:
            url += "?"
        else:
            url += "&"
        return url + "apikey=" + self.KEY
    
    def __build_url__(self, query:dict[str, str]) -> str:
        if query is None or len(query) == 0:
            raise ValueError("At least one query parameter must be given")
        url = self.QUERY_URL_BASE
        for i, (key, value) in enumerate(query.items()):
            url += (f"{'' if i == 0 else '&'}{key}={value}")
        return self.__append_key__(url)

        