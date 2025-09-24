import logging
from typing import Optional
from datetime import datetime

import dotenv
import pandas as pd
from polygon import RESTClient

import app.utils.dates as dates
from app.services.clients.client_utils import ratelimit

L = logging.getLogger(__name__)
class PolygonClient():
    """
    Client class to interact with polygon API
    """

    def __init__(self) -> None:
        self.KEY = dotenv.get_key(".env", "POLYGON_API_KEY")
        if self.KEY is None: 
            raise Exception("No API key found")
        self.REST = RESTClient(self.KEY)

    @ratelimit()
    async def getDMS(self, adjusted: bool = True) -> Optional[pd.DataFrame]:
        # TODO - implement a way to get data against the most recent day
        try:
            resp = self.REST.get_grouped_daily_aggs(
                "2025-09-12",
                adjusted = adjusted
            )
            return pd.DataFrame([obj.__dict__ for obj in resp])
        except Exception as e:
            L.exception(e)
            return pd.DataFrame()
    
    @ratelimit()
    async def getDetails(self, ticker: str) -> Optional[pd.DataFrame]:
        try:
            resp = self.REST.get_ticker_details(ticker=ticker)
            return pd.DataFrame([resp.__dict__])
        except Exception as e:
            L.exception(e)
            return pd.DataFrame()
        
    @ratelimit()
    async def getSMA(self, ticker:str, window:int=50) -> Optional[pd.DataFrame]:
        try:
            resp = self.REST.get_sma(
                ticker=ticker,
                timespan="day",
                adjusted="true",
                window=window,
                series_type="close",
                order="desc",
                limit=5000,
            )
            df = pd.DataFrame([obj.__dict__ for obj in resp.values])
            df = df.dropna()
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
            
            return df
        except Exception as e:
            L.exception(e)
            return pd.DataFrame()