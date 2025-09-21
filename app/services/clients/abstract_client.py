import asyncio
import time


DEFAULT_RL_DELAY = 0.1

class AbstractClient:
    """
        Class with general-purpose methods to be inherited by other clients
    """
    def __init__(self, rl_delay: float) -> None:
        #Rate limiting
        self.sec_since_last_req = 0
        self.rl_delay = rl_delay

    async def _rate_limit(self):
        """
        Implement rate limiting for API requests.
        """
        current_time = time.time()
        
        if current_time - self.sec_since_last_req < self.rl_delay:
            await asyncio.sleep(self.rl_delay)
