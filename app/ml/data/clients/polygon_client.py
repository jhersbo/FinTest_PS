from typing import Optional
from requests import get

import pandas as pd
from polygon import RESTClient
import numpy as np

from .client_utils import ratelimit
from app.core.utils.logger import get_logger
from ....core.config.config import get_config

L = get_logger(__name__)
class PolygonClient():
    """
    Client class to interact with polygon API
    """

    URL_BASE = "https://api.polygon.io"

    def __init__(self) -> None:
        CONFIG = get_config()
        self.KEY = CONFIG.polygon_api_key
        if self.KEY is None: 
            raise Exception("No API key found")
        self.REST = RESTClient(self.KEY, verbose=True)

    @ratelimit()
    async def getTickerInfo(self, market:str, active:bool=True, order:str="asc", limit:int=1000, sort_field:str="ticker") -> list[dict[str,str]]:
        """
        Returns basic information for each tradable ticker for a given market. 
        As of now, we can make a limited number of requests per minute,
        so each call to the polygon api is rate limited quite slowly.
        """
        valid = [
            "stocks",
            "crypto",
            "fx",
            "otc",
            "indices"
        ]
        if market is None:
            raise ValueError("Market type must be provided")
        if valid.count(market) == 0:
            raise ValueError("Invalid market type")
        PATH = "v3/reference/tickers"
        query = {
            "market": market,
            "active": str(active).lower(),
            "order": order,
            "limit": limit,
            "sort": sort_field
        }
        url = self.__build_url__(path=PATH, query=query)
        return await self.get_and_append([], url, data_path="results", next_path="next_url", rl=20)



    @ratelimit()
    async def getDMS(self, adjusted: bool = True) -> Optional[pd.DataFrame]:
        # TODO - implement a way to get data against the most recent day
        resp = self.REST.get_grouped_daily_aggs(
            "2025-09-12",
            adjusted = adjusted
        )
        df = pd.DataFrame([obj.__dict__ for obj in resp])
        df = df.replace(np.nan, value=None)

        return df
    
    @ratelimit()
    async def getDetails(self, ticker: str) -> Optional[pd.DataFrame]:
        resp = self.REST.get_ticker_details(ticker=ticker)
        df = pd.DataFrame([resp.__dict__])
        df = df.replace(np.nan, None)
        
        return df
        
    @ratelimit()
    async def getSMA(self, ticker:str, window:int=50, limit:int=5000) -> Optional[pd.DataFrame]:
        resp = self.REST.get_sma(
            ticker=ticker,
            timespan="day",
            adjusted="true",
            window=window,
            series_type="close",
            order="desc",
            limit=limit,
        )
        df = pd.DataFrame([obj.__dict__ for obj in resp.values])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
        df = df.replace(np.nan, None)

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
        return url + "apiKey=" + self.KEY
    
    def __build_url__(self, path:str, query:dict[str, str]) -> str:
        if path is None:
            raise ValueError("URL path must be provided")
        if query is None or len(query) == 0:
            raise ValueError("At least one query parameter must be given")
        url = self.URL_BASE + ("" if path[0] == "/" else "/") + path
        for i, (key, value) in enumerate(query.items()):
            url += (f"{'?' if i == 0 else '&'}{key}={value}")
        return self.__append_key__(url)
    
    async def get_and_append(self, agg:list[any], url:str, data_path:str, next_path:str="next_url", rl:float=0.1) -> list[any]:
        """
        Makes a request at the url and continues making requests until 'next_path' is exhausted.
        Will accumulate results on the given list. Can pass a rate limit value for the request
        """
        @ratelimit(rl_limit=rl)
        async def innner(agg:list[any], url:str, data_path:str, next_path:str):
            L.info(f"Making request to {url}")
            json = get(url=url).json()
            if json["status"] and json["status"] == "ERROR":
                L.error(json["error"])
                raise Exception("Error in API call")
            agg.extend(json[data_path])
            if json.get(next_path) is not None and len(json[next_path]) > 0:
                return await innner(agg, self.__append_key__(json[next_path]), data_path, next_path)
            return agg

        return await innner(agg, url, data_path, next_path)
