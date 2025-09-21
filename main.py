import asyncio
import logging
from dotenv import load_dotenv
from app.services.clients.polygon_client import PolygonClient
from app.utils.dates import *


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Init env
loaded = load_dotenv()

async def testAsync():
    p = PolygonClient()
    
    df = await p.getDMS()
    # df = await p.getDetails("AAPL")

    print(df)

def testSync():
    print(today_minus_days(21))
    


if __name__ == "__main__":
    asyncio.run(testAsync())
    # testSync()