"""
Test script for the data pipeline.
Run this to verify that data collection is working correctly.
"""

import asyncio
import logging
import os
from app.services.data_service import DataService
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Init env
loaded = load_dotenv()

async def test_data_pipeline():
    """Test the data pipeline with sample data."""

    # Initialize data service
    data_service = DataService()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing data collection for {symbol}")
        logger.info(f"{'='*50}")
        
        try:
            # Test stock data collection
            logger.info("1. Testing stock data collection...")
            stock_data = await data_service.get_stock_data(symbol, period="1mo")
            
            if stock_data is not None and not stock_data.empty:
                logger.info(f"✅ Stock data collected successfully!")
                logger.info(f"   Records: {len(stock_data)}")
                logger.info(f"   Date range: {stock_data.index[0].date()} to {stock_data.index[-1].date()}")
                logger.info(f"   Latest close: ${stock_data['Close'].iloc[-1]:.2f}")
            else:
                logger.error("❌ Failed to collect stock data")
            
            # Test technical indicators (only if we have a real API key)
            logger.info("2. Testing technical indicators...")
            technical_data = await data_service.get_technical_indicators(symbol)
            
            if technical_data:
                logger.info(f"✅ Technical indicators collected successfully!")
                for indicator, value in technical_data.items():
                    if isinstance(value, dict):
                        logger.info(f"   {indicator}: {list(value.keys())}")
                    else:
                        logger.info(f"   {indicator}: {value}")

            # Test news sentiment (only if we have a real API key)
            logger.info("3. Testing news sentiment...")
            sentiment_data = await data_service.get_news_sentiment(symbol, days=7)
            
            if sentiment_data:
                logger.info(f"✅ News sentiment collected successfully!")
                logger.info(f"   Sentiment score: {sentiment_data.get('sentiment_score', 0):.3f}")
                logger.info(f"   Article count: {sentiment_data.get('article_count', 0)}")
                
                distribution = sentiment_data.get('sentiment_distribution', {})
                logger.info(f"   Distribution: {distribution}")
            else:
                logger.warning("⚠️ No sentiment data collected")
            # Test comprehensive data collection
            logger.info("4. Testing comprehensive data collection...")
            comprehensive_data = await data_service.get_comprehensive_data(symbol, period="1mo")
            
            if comprehensive_data:
                logger.info(f"✅ Comprehensive data collected successfully!")
                completeness = comprehensive_data.get('data_completeness', {})
                logger.info(f"   Data completeness: {completeness}")
            else:
                logger.error("❌ Failed to collect comprehensive data")
                
        except Exception as e:
            logger.error(f"❌ Error testing {symbol}: {str(e)}")
        
        # Add delay between symbols to respect rate limits
        await asyncio.sleep(1)
    
    logger.info(f"\n{'='*50}")
    logger.info("Data pipeline test completed!")
    logger.info(f"{'='*50}")


async def test_single_symbol(symbol: str = 'AAPL'):
    """Test a single symbol in detail."""

    data_service = DataService()
    
    logger.info(f"Testing {symbol} in detail...")
    
    # Get comprehensive data
    data = await data_service.get_comprehensive_data(symbol, period="1mo")
    
    if data:
        logger.info("✅ Data collected successfully!")
        
        # Print stock data summary
        if data['stock_data'] is not None:
            stock_df = data['stock_data']
            logger.info(f"Stock Data Summary:")
            logger.info(f"  - Records: {len(stock_df)}")
            logger.info(f"  - Date range: {stock_df.index[0].date()} to {stock_df.index[-1].date()}")
            logger.info(f"  - Latest close: ${stock_df['Close'].iloc[-1]:.2f}")
            logger.info(f"  - Volume: {stock_df['Volume'].iloc[-1]:,}")
        
        # Print technical indicators
        if data['technical_indicators']:
            logger.info(f"Technical Indicators:")
            for indicator, value in data['technical_indicators'].items():
                logger.info(f"  - {indicator}: {value}")
        
        # Print sentiment
        if data['sentiment']:
            sentiment = data['sentiment']
            logger.info(f"Sentiment Analysis:")
            logger.info(f"  - Score: {sentiment.get('sentiment_score', 0):.3f}")
            logger.info(f"  - Articles: {sentiment.get('article_count', 0)}")
            
            # Print a few recent articles
            articles = sentiment.get('articles', [])[:3]
            for i, article in enumerate(articles, 1):
                logger.info(f"  - Article {i}: {article.get('title', 'No title')[:50]}...")
    else:
        logger.error("❌ Failed to collect data")


if __name__ == "__main__":
    # Test multiple symbols
    asyncio.run(test_data_pipeline())
    
    # Test single symbol in detail
    # asyncio.run(test_single_symbol('AAPL'))
