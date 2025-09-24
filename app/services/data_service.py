"""
Data collection service for market data, sentiment, and technical indicators.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import dotenv
import pandas as pd
import requests
import yfinance as yf
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.timeseries import TimeSeries

logger = logging.getLogger(__name__)


class DataService:
    """Service for collecting and managing market data from various sources."""
    
    def __init__(self):
        """
        Initialize the data service.
        
        Args:
            alpha_vantage_api_key: API key for Alpha Vantage
            news_api_key: API key for NewsAPI
        """
        self.alpha_vantage_api_key = dotenv.get_key('.env', 'ALPHA_VANTAGE_API_KEY')
        self.news_api_key = dotenv.get_key('.env', 'NEWS_API_KEY')

        # Initialize API clients
        self.ts = TimeSeries(key=self.alpha_vantage_api_key, output_format='pandas')
        self.ti = TechIndicators(key=self.alpha_vantage_api_key, output_format='pandas')
        
        # Rate limiting
        self.last_yahoo_request = 0
        self.last_alpha_vantage_request = 0
        self.last_news_request = 0
        self.request_delay = 0.1  # 100ms between requests

        
    # async def get_stock_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
    #     """
    #     Get historical stock data from Yahoo Finance.
        
    #     Args:
    #         symbol: Stock symbol (e.g., 'AAPL')
    #         period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
    #     Returns:
    #         DataFrame with OHLCV data or None if error
    #     """
    #     try:
    #         # Rate limiting
    #         await self._rate_limit('yahoo')
            
    #         logger.info(f"Fetching stock data for {symbol} for period {period}")
            
    #         # Get data from Yahoo Finance
    #         ticker = yf.Ticker(symbol)
    #         data = ticker.history(period=period)
            
    #         if data.empty:
    #             logger.warning(f"No data returned for {symbol}")
    #             return None
                
    #         # Clean and format data
    #         data = self._clean_stock_data(data)
            
    #         logger.info(f"Successfully fetched {len(data)} records for {symbol}")
    #         return data
            
    #     except Exception as e:
    #         logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
    #         return None
    
    # async def get_technical_indicators(self, symbol: str) -> Dict[str, Any]:
    #     """
    #     Get technical indicators from Alpha Vantage.
        
    #     Args:
    #         symbol: Stock symbol
            
    #     Returns:
    #         Dictionary with technical indicators
    #     """
    #     try:
    #         # Rate limiting
    #         await self._rate_limit('alpha_vantage')
            
    #         logger.info(f"Fetching technical indicators for {symbol}")
            
    #         indicators = {}
            
    #         # RSI
    #         try:
    #             rsi_data, _ = self.ti.get_rsi(symbol=symbol, interval='daily', time_period=14, series_type='close')
    #             if not rsi_data.empty:
    #                 indicators['rsi'] = rsi_data.iloc[-1]['RSI']
    #         except Exception as e:
    #             logger.warning(f"Could not fetch RSI for {symbol}: {str(e)}")
            
    #         # MACD - TODO: this is a premium endpoint, so we're not going to use it for now
    #         # try:
    #         #     macd_data, _ = self.ti.get_macd(symbol=symbol, interval='daily', series_type='close')
    #         #     if not macd_data.empty:
    #         #         latest = macd_data.iloc[-1]
    #         #         indicators['macd'] = {
    #         #             'macd': latest['MACD'],
    #         #             'macd_signal': latest['MACD_Signal'],
    #         #             'macd_hist': latest['MACD_Hist']
    #         #         }
    #         # except Exception as e:
    #         #     logger.warning(f"Could not fetch MACD for {symbol}: {str(e)}")
            
    #         # Bollinger Bands
    #         try:
    #             bb_data, _ = self.ti.get_bbands(symbol=symbol, interval='daily', time_period=20, series_type='close')
    #             if not bb_data.empty:
    #                 latest = bb_data.iloc[-1]
    #                 indicators['bollinger_bands'] = {
    #                     'upper': latest['Real Upper Band'],
    #                     'middle': latest['Real Middle Band'],
    #                     'lower': latest['Real Lower Band']
    #                 }
    #         except Exception as e:
    #             logger.warning(f"Could not fetch Bollinger Bands for {symbol}: {str(e)}")
            
    #         # Moving Averages
    #         try:
    #             sma_data, _ = self.ti.get_sma(symbol=symbol, interval='daily', time_period=20, series_type='close')
    #             if not sma_data.empty:
    #                 indicators['sma_20'] = sma_data.iloc[-1]['SMA']
    #         except Exception as e:
    #             logger.warning(f"Could not fetch SMA for {symbol}: {str(e)}")
            
    #         logger.info(f"Successfully fetched {len(indicators)} technical indicators for {symbol}")
    #         return indicators
            
    #     except Exception as e:
    #         logger.error(f"Error fetching technical indicators for {symbol}: {str(e)}")
    #         return {}
    
    # async def get_news_sentiment(self, symbol: str, days: int = 7) -> Dict[str, Any]:
    #     """
    #     Get news sentiment for a stock symbol.
        
    #     Args:
    #         symbol: Stock symbol
    #         days: Number of days to look back
            
    #     Returns:
    #         Dictionary with sentiment analysis
    #     """
    #     try:
    #         # Rate limiting
    #         await self._rate_limit('news')
            
    #         logger.info(f"Fetching news sentiment for {symbol}")
            
    #         # Calculate date range
    #         end_date = datetime.now()
    #         start_date = end_date - timedelta(days=days)
            
    #         # NewsAPI query
    #         url = "https://newsapi.org/v2/everything"
    #         params = {
    #             'q': f'"{symbol}" OR "{symbol} stock"',
    #             'from': start_date.strftime('%Y-%m-%d'),
    #             'to': end_date.strftime('%Y-%m-%d'),
    #             'language': 'en',
    #             'sortBy': 'publishedAt',
    #             'apiKey': self.news_api_key
    #         }
            
    #         response = requests.get(url, params=params)
    #         response.raise_for_status()
            
    #         data = response.json()
            
    #         if data['status'] != 'ok':
    #             logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
    #             return {}
            
    #         articles = data.get('articles', [])
            
    #         if not articles:
    #             logger.warning(f"No news articles found for {symbol}")
    #             return {
    #                 'sentiment_score': 0.0,
    #                 'article_count': 0,
    #                 'articles': []
    #             }
            
    #         # Simple sentiment analysis (can be enhanced later)
    #         sentiment_scores = []
    #         processed_articles = []
            
    #         for article in articles[:20]:  # Limit to 20 articles
    #             # Simple keyword-based sentiment
    #             title = article.get('title', '').lower()
    #             description = article.get('description', '').lower()
    #             content = f"{title} {description}"
                
    #             # Basic sentiment keywords
    #             positive_words = ['up', 'rise', 'gain', 'positive', 'bullish', 'growth', 'profit', 'earnings beat']
    #             negative_words = ['down', 'fall', 'drop', 'negative', 'bearish', 'loss', 'decline', 'earnings miss']
                
    #             positive_count = sum(1 for word in positive_words if word in content)
    #             negative_count = sum(1 for word in negative_words if word in content)
                
    #             if positive_count > negative_count:
    #                 sentiment = 0.5
    #             elif negative_count > positive_count:
    #                 sentiment = -0.5
    #             else:
    #                 sentiment = 0.0
                
    #             sentiment_scores.append(sentiment)
                
    #             processed_articles.append({
    #                 'title': article.get('title'),
    #                 'description': article.get('description'),
    #                 'url': article.get('url'),
    #                 'published_at': article.get('publishedAt'),
    #                 'sentiment': sentiment
    #             })
            
    #         # Calculate overall sentiment
    #         overall_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
    #         result = {
    #             'sentiment_score': overall_sentiment,
    #             'article_count': len(processed_articles),
    #             'articles': processed_articles,
    #             'sentiment_distribution': {
    #                 'positive': len([s for s in sentiment_scores if s > 0]),
    #                 'negative': len([s for s in sentiment_scores if s < 0]),
    #                 'neutral': len([s for s in sentiment_scores if s == 0])
    #             }
    #         }
            
    #         logger.info(f"Successfully fetched news sentiment for {symbol}: {overall_sentiment:.3f}")
    #         return result
            
    #     except Exception as e:
    #         logger.error(f"Error fetching news sentiment for {symbol}: {str(e)}")
    #         return {}
    
    # async def get_comprehensive_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
    #     """
    #     Get comprehensive data for a symbol including price data, technical indicators, and sentiment.
        
    #     Args:
    #         symbol: Stock symbol
    #         period: Time period for historical data
            
    #     Returns:
    #         Dictionary with all data
    #     """
    #     logger.info(f"Fetching comprehensive data for {symbol}")
        
    #     # Fetch all data concurrently
    #     tasks = [
    #         self.get_stock_data(symbol, period),
    #         self.get_technical_indicators(symbol),
    #         self.get_news_sentiment(symbol)
    #     ]
        
    #     results = await asyncio.gather(*tasks, return_exceptions=True)
        
    #     # Process results
    #     stock_data, technical_data, sentiment_data = results
        
    #     # Handle exceptions
    #     if isinstance(stock_data, Exception):
    #         logger.error(f"Error in stock data: {stock_data}")
    #         stock_data = None
    #     if isinstance(technical_data, Exception):
    #         logger.error(f"Error in technical data: {technical_data}")
    #         technical_data = {}
    #     if isinstance(sentiment_data, Exception):
    #         logger.error(f"Error in sentiment data: {sentiment_data}")
    #         sentiment_data = {}
        
    #     return {
    #         'symbol': symbol,
    #         'timestamp': datetime.now().isoformat(),
    #         'stock_data': stock_data,
    #         'technical_indicators': technical_data,
    #         'sentiment': sentiment_data,
    #         'data_completeness': {
    #             'stock_data': stock_data is not None,
    #             'technical_indicators': len(technical_data) > 0,
    #             'sentiment': len(sentiment_data) > 0
    #         }
    #     }
    
    def _clean_stock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and format stock data.
        
        Args:
            data: Raw stock data
            
        Returns:
            Cleaned DataFrame
        """
        # Remove any rows with NaN values
        data = data.dropna()
        
        # Ensure we have the required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_columns):
            logger.warning("Missing required columns in stock data")
            return pd.DataFrame()
        
        # Convert to numeric types
        for col in required_columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Remove any remaining NaN values
        data = data.dropna()
        
        # Sort by date
        data = data.sort_index()
        
        return data
    
    async def _rate_limit(self, source: str):
        """
        Implement rate limiting for API requests.
        
        Args:
            source: API source ('yahoo', 'alpha_vantage', 'news')
        """
        current_time = time.time()
        
        if source == 'yahoo':
            if current_time - self.last_yahoo_request < self.request_delay:
                await asyncio.sleep(self.request_delay)
            self.last_yahoo_request = current_time
        elif source == 'alpha_vantage':
            if current_time - self.last_alpha_vantage_request < self.request_delay:
                await asyncio.sleep(self.request_delay)
            self.last_alpha_vantage_request = current_time
        elif source == 'news':
            if current_time - self.last_news_request < self.request_delay:
                await asyncio.sleep(self.request_delay)
            self.last_news_request = current_time
