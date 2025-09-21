from typing import Optional
import pandas as pd
import dotenv
from polygon import RESTClient
from app.services.clients.abstract_client import AbstractClient, DEFAULT_RL_DELAY
from app.utils.dates import today, today_minus_days

class PolygonClient(AbstractClient):
    """
        Client class to interact with polygon API
    """

    def __init__(self, rl_delay: float = DEFAULT_RL_DELAY) -> None:
        super().__init__(rl_delay)

        self.KEY = dotenv.get_key(".env", "POLYGON_API_KEY")
        if self.KEY is None: 
            raise Exception("No API key found")
        self.REST = RESTClient(self.KEY)

    async def getDMS(self, adjusted: bool = True) -> Optional[pd.DataFrame]:
        await super()._rate_limit()

        resp = self.REST.get_grouped_daily_aggs(
            today_minus_days(2), # TODO: Come back to this
            adjusted = adjusted
        )

        return pd.DataFrame([obj.__dict__ for obj in resp])
    
    async def getDetails(self, ticker: str) -> Optional[pd.DataFrame]:
        await super()._rate_limit()

        resp = self.REST.get_ticker_details(ticker=ticker)

        return pd.DataFrame([resp.__dict__])