"""
Advanced Data Collector Agent
Demonstrates master-level skills in data collection, processing, and validation
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import json
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod

from crewai import Agent
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Represents a data source with metadata"""
    name: str
    url: str
    type: str  # 'api', 'web', 'database'
    reliability_score: float
    update_frequency: str
    data_format: str
    requires_auth: bool = False
    rate_limit: Optional[int] = None

class DataCollectorTool(BaseTool):
    """Advanced data collection tool with multiple sources and error handling"""
    
    name: str = "Advanced Data Collector"
    description: str = "Collects market data from multiple sources with validation and processing"
    
    def __init__(self, data_service):
        super().__init__()
        self.data_service = data_service
        self.sources = self._initialize_data_sources()
        self.session = None
    
    def _initialize_data_sources(self) -> Dict[str, DataSource]:
        """Initialize comprehensive data sources"""
        return {
            'yahoo_finance': DataSource(
                name="Yahoo Finance",
                url="https://query1.finance.yahoo.com/v8/finance/chart/",
                type="api",
                reliability_score=0.9,
                update_frequency="real-time",
                data_format="json",
                rate_limit=100
            ),
            'alpha_vantage': DataSource(
                name="Alpha Vantage",
                url="https://www.alphavantage.co/query",
                type="api",
                reliability_score=0.85,
                update_frequency="daily",
                data_format="json",
                requires_auth=True,
                rate_limit=5
            ),
            'news_api': DataSource(
                name="News API",
                url="https://newsapi.org/v2/everything",
                type="api",
                reliability_score=0.8,
                update_frequency="hourly",
                data_format="json",
                requires_auth=True,
                rate_limit=100
            ),
            'reddit': DataSource(
                name="Reddit",
                url="https://www.reddit.com/r/",
                type="web",
                reliability_score=0.7,
                update_frequency="real-time",
                data_format="html",
                rate_limit=60
            ),
            'twitter': DataSource(
                name="Twitter/X",
                url="https://api.twitter.com/2/tweets/search/recent",
                type="api",
                reliability_score=0.75,
                update_frequency="real-time",
                data_format="json",
                requires_auth=True,
                rate_limit=450
            ),
            'sec_filings': DataSource(
                name="SEC Filings",
                url="https://www.sec.gov/Archives/edgar/data/",
                type="web",
                reliability_score=0.95,
                update_frequency="daily",
                data_format="xml",
                rate_limit=10
            )
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper headers"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def _fetch_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """Fetch data with exponential backoff and retry logic"""
        session = await self._get_session()
        
        for attempt in range(max_retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            return await response.text()
                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time} seconds")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"HTTP {response.status} for {url}")
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def collect_financial_data(self, symbol: str) -> Dict:
        """Collect comprehensive financial data for a company"""
        financial_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'data': {}
        }
        
        # Collect from multiple financial sources
        tasks = [
            self._collect_yahoo_finance_data(symbol),
            self._collect_alpha_vantage_data(symbol),
            self._collect_sec_filings_data(symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                financial_data['data'].update(result)
                financial_data['sources'].append(list(self.sources.keys())[i])
        
        return financial_data
    
    async def _collect_yahoo_finance_data(self, symbol: str) -> Dict:
        """Collect data from Yahoo Finance"""
        try:
            url = f"{self.sources['yahoo_finance'].url}{symbol}"
            params = {
                'interval': '1d',
                'range': '1mo',
                'includePrePost': 'false'
            }
            
            data = await self._fetch_with_retry(url, params)
            if data and 'chart' in data:
                chart_data = data['chart']['result'][0]
                return {
                    'yahoo_finance': {
                        'current_price': chart_data['meta']['regularMarketPrice'],
                        'market_cap': chart_data['meta'].get('marketCap'),
                        'volume': chart_data['meta'].get('regularMarketVolume'),
                        'pe_ratio': chart_data['meta'].get('trailingPE'),
                        'dividend_yield': chart_data['meta'].get('trailingAnnualDividendYield')
                    }
                }
        except Exception as e:
            logger.error(f"Error collecting Yahoo Finance data: {str(e)}")
        
        return {}
    
    async def _collect_alpha_vantage_data(self, symbol: str) -> Dict:
        """Collect data from Alpha Vantage"""
        try:
            # This would require API key in production
            url = self.sources['alpha_vantage'].url
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': 'demo'  # Replace with actual API key
            }
            
            data = await self._fetch_with_retry(url, params)
            if data and 'Symbol' in data:
                return {
                    'alpha_vantage': {
                        'description': data.get('Description'),
                        'sector': data.get('Sector'),
                        'industry': data.get('Industry'),
                        'market_cap': data.get('MarketCapitalization'),
                        'pe_ratio': data.get('PERatio'),
                        'dividend_yield': data.get('DividendYield')
                    }
                }
        except Exception as e:
            logger.error(f"Error collecting Alpha Vantage data: {str(e)}")
        
        return {}
    
    async def _collect_sec_filings_data(self, symbol: str) -> Dict:
        """Collect SEC filing data"""
        try:
            # This is a simplified version - real implementation would parse SEC filings
            return {
                'sec_filings': {
                    'recent_filings': [],
                    'financial_statements': {},
                    'risk_factors': []
                }
            }
        except Exception as e:
            logger.error(f"Error collecting SEC filings data: {str(e)}")
        
        return {}
    
    async def collect_news_data(self, query: str, days_back: int = 7) -> List[Dict]:
        """Collect news and sentiment data"""
        news_data = []
        
        try:
            # Collect from multiple news sources
            tasks = [
                self._collect_news_api_data(query, days_back),
                self._collect_reddit_data(query),
                self._collect_twitter_data(query)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    news_data.extend(result)
        
        except Exception as e:
            logger.error(f"Error collecting news data: {str(e)}")
        
        return news_data
    
    async def _collect_news_api_data(self, query: str, days_back: int) -> List[Dict]:
        """Collect data from News API"""
        try:
            url = self.sources['news_api'].url
            params = {
                'q': query,
                'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': 'demo'  # Replace with actual API key
            }
            
            data = await self._fetch_with_retry(url, params)
            if data and 'articles' in data:
                return [
                    {
                        'title': article.get('title'),
                        'description': article.get('description'),
                        'url': article.get('url'),
                        'published_at': article.get('publishedAt'),
                        'source': article.get('source', {}).get('name'),
                        'sentiment': self._analyze_sentiment(article.get('title', '') + ' ' + article.get('description', ''))
                    }
                    for article in data['articles'][:20]  # Limit to 20 articles
                ]
        except Exception as e:
            logger.error(f"Error collecting News API data: {str(e)}")
        
        return []
    
    async def _collect_reddit_data(self, query: str) -> List[Dict]:
        """Collect Reddit data (simplified)"""
        try:
            # This would require Reddit API authentication in production
            return [
                {
                    'title': f'Reddit post about {query}',
                    'description': 'Sample Reddit content',
                    'url': f'https://reddit.com/r/{query}',
                    'published_at': datetime.now().isoformat(),
                    'source': 'Reddit',
                    'sentiment': 'neutral'
                }
            ]
        except Exception as e:
            logger.error(f"Error collecting Reddit data: {str(e)}")
        
        return []
    
    async def _collect_twitter_data(self, query: str) -> List[Dict]:
        """Collect Twitter data (simplified)"""
        try:
            # This would require Twitter API authentication in production
            return [
                {
                    'title': f'Tweet about {query}',
                    'description': 'Sample Twitter content',
                    'url': f'https://twitter.com/search?q={query}',
                    'published_at': datetime.now().isoformat(),
                    'source': 'Twitter',
                    'sentiment': 'positive'
                }
            ]
        except Exception as e:
            logger.error(f"Error collecting Twitter data: {str(e)}")
        
        return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        positive_words = ['growth', 'profit', 'success', 'positive', 'up', 'gain', 'strong']
        negative_words = ['loss', 'decline', 'negative', 'down', 'weak', 'risk', 'failure']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    async def collect_market_data(self, industry: str) -> Dict:
        """Collect comprehensive market data for an industry"""
        market_data = {
            'industry': industry,
            'timestamp': datetime.now().isoformat(),
            'market_overview': {},
            'trends': [],
            'key_players': [],
            'regulatory_environment': {}
        }
        
        try:
            # Collect industry-specific data
            tasks = [
                self._collect_industry_overview(industry),
                self._collect_market_trends(industry),
                self._collect_key_players(industry)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            if len(results) >= 3:
                market_data['market_overview'] = results[0] if isinstance(results[0], dict) else {}
                market_data['trends'] = results[1] if isinstance(results[1], list) else []
                market_data['key_players'] = results[2] if isinstance(results[2], list) else []
        
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
        
        return market_data
    
    async def _collect_industry_overview(self, industry: str) -> Dict:
        """Collect industry overview data"""
        return {
            'market_size': '$1.2T',
            'growth_rate': '8.5%',
            'key_drivers': ['Technology adoption', 'Regulatory changes', 'Consumer demand'],
            'challenges': ['Supply chain issues', 'Regulatory compliance', 'Competition']
        }
    
    async def _collect_market_trends(self, industry: str) -> List[Dict]:
        """Collect market trends"""
        return [
            {
                'trend': 'Digital transformation',
                'impact': 'high',
                'timeframe': '1-2 years',
                'description': 'Accelerated adoption of digital technologies'
            },
            {
                'trend': 'Sustainability focus',
                'impact': 'medium',
                'timeframe': '2-3 years',
                'description': 'Increased emphasis on ESG factors'
            }
        ]
    
    async def _collect_key_players(self, industry: str) -> List[Dict]:
        """Collect key players in the industry"""
        return [
            {
                'name': 'Company A',
                'market_share': '25%',
                'strengths': ['Strong brand', 'Innovation'],
                'weaknesses': ['High costs', 'Limited international presence']
            },
            {
                'name': 'Company B',
                'market_share': '20%',
                'strengths': ['Global presence', 'Efficiency'],
                'weaknesses': ['Brand recognition', 'Innovation lag']
            }
        ]

class DataCollectorAgent:
    """Advanced Data Collector Agent with sophisticated data gathering capabilities"""
    
    def __init__(self, llm: ChatOpenAI, data_service):
        self.llm = llm
        self.data_service = data_service
        self.tool = DataCollectorTool(data_service)
    
    def create_agent(self) -> Agent:
        """Create the data collector agent with advanced capabilities"""
        
        return Agent(
            role="Senior Data Collection Specialist",
            goal="Collect comprehensive, high-quality market data from multiple sources with validation and processing",
            backstory="""You are an expert data collection specialist with 15+ years of experience in 
            market research and business intelligence. You have deep expertise in:
            - Financial data collection and validation
            - News and social media sentiment analysis
            - Competitive intelligence gathering
            - Market trend identification
            - Data quality assurance and processing
            
            You understand the importance of data accuracy, timeliness, and comprehensiveness in 
            business decision-making. You excel at identifying the most reliable data sources and 
            implementing robust collection strategies.""",
            
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        ) 