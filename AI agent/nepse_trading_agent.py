import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import numpy as np
import pandas as pd
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
import json
import logging
from dotenv import load_dotenv
import httpx
import talib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import asyncpg
import redis.asyncio as redis
from fastapi import HTTPException
from langchain.agents.output_parsers import ReActSingleInputOutputParser
import concurrent.futures

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingAgentError(Exception):
    """Base exception for trading agent errors"""
    pass

class DataFetchError(TradingAgentError):
    """Error fetching data"""
    pass

class AnalysisError(TradingAgentError):
    """Error during analysis"""
    pass

class PerplexitySearchTool:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.url = "https://api.perplexity.ai/chat/completions"
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        masked_key = self.api_key[:4] + "..." + self.api_key[-4:]
        logger.info(f"[Perplexity] Using API key: {masked_key}")

    @staticmethod
    def test_api_key_and_models():
        import requests
        import os
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        for model in ["sonar-deep-research", "sonar-small-chat"]:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Test."},
                    {"role": "user", "content": "Hello, world!"}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            }
            print(f"Trying model: {model}")
            response = requests.post(url, headers=headers, json=payload)
            print(response.status_code, response.text)

    async def _search_async(self, query: str) -> str:
        # Try deep research model first, fallback to small chat if 401
        for model in ["sonar-deep-research", "sonar-small-chat"]:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Conduct comprehensive research and provide detailed analysis."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 8000 if model == "sonar-deep-research" else 2048,
                "temperature": 0.7
            }
            logger.info(f"[Perplexity] Trying model: {model}")
            logger.info(f"[Perplexity] Payload: {json.dumps(payload)}")
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(self.url, headers=headers, json=payload, timeout=60.0)
                    logger.info(f"Perplexity API status: {response.status_code}")
                    logger.info(f"Perplexity API headers: {dict(response.headers)}")
                    response.raise_for_status()
                    result = response.json()
                    logger.info("Deep Research completed successfully!")
                    logger.info(f"Response: {json.dumps(result, indent=2)}")
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if not content:
                        logger.error("Perplexity API returned no content.")
                        raise RuntimeError("Perplexity API returned no content.")
                    return content
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401 and model == "sonar-deep-research":
                        logger.warning("401 Unauthorized for sonar-deep-research, retrying with sonar-small-chat...")
                        continue
                    logger.error(f"Error during Perplexity API call: {repr(e)}")
                    if hasattr(e, 'response') and e.response is not None:
                        logger.error(f"Error details: {e.response.text}")
                    raise RuntimeError(f"Perplexity API error: {repr(e)}")
                except Exception as e:
                    logger.error(f"Error during Perplexity API call: {repr(e)}")
                    if hasattr(e, 'response') and e.response is not None:
                        logger.error(f"Error details: {e.response.text}")
                    raise RuntimeError(f"Perplexity API error: {repr(e)}")
        raise RuntimeError("Perplexity API error: Unauthorized for all models.")

    def search(self, query: str) -> str:
        future = self._executor.submit(lambda: asyncio.run(self._search_async(query)))
        return future.result()

class NepseTradingAgent:
    def __init__(self, pg_conn, redis_conn):
        if not pg_conn or not redis_conn:
            raise ValueError("Database connections are required")
            
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4")
        self.perplexity_search = PerplexitySearchTool()
        self.wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        self.embeddings = OpenAIEmbeddings()
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        self.pg_conn = pg_conn
        self.redis_conn = redis_conn
        
        # Initialize tools with error handling
        try:
            self.tools = [
                Tool(
                    name="TechnicalAnalysis",
                    func=self.perform_technical_analysis,
                    description="Perform technical analysis on stock data"
                ),
                Tool(
                    name="FundamentalAnalysis",
                    func=self.perform_fundamental_analysis,
                    description="Analyze fundamental factors"
                ),
                Tool(
                    name="PerplexitySearch",
                    func=self.perplexity_search.search,
                    description="Perform deep research or search using Perplexity AI API"
                ),
                Tool(
                    name="MarketBehavior",
                    func=self.analyze_market_behavior,
                    description="Analyze market behavior and patterns"
                )
            ]
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}")
            raise TradingAgentError("Failed to initialize trading tools")
        
        # Initialize agent
        try:
            self.agent = self._create_agent()
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise TradingAgentError("Failed to create trading agent")

    def _create_agent(self):
        prompt = TradingSignalPromptTemplate(
            tools=self.tools,
            template="""
            You are a sophisticated NEPSE stock market trading signal generator. Your task is to:
            1. Analyze technical indicators and patterns
            2. Evaluate fundamental factors
            3. Assess news sentiment and market behavior
            4. Generate trading signals with clear reasoning
            5. Provide entry/exit points and timeframes
            6. Validate signals with multiple factors
            
            Use the following tools:
            {tools}
            
            Current conversation:
            {chat_history}
            
            Human: {input}
            {agent_scratchpad}
            """
        )
        
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=ReActSingleInputOutputParser(),
            allowed_tools=[tool.name for tool in self.tools],
            stop=["\nObservation:"],
            memory=self.memory
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            verbose=True,
            memory=self.memory
        )

    async def get_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch historical data for analysis"""
        if not symbol:
            raise ValueError("Stock symbol is required")
            
        if days <= 0:
            raise ValueError("Days must be positive")
            
        try:
            query = """
                SELECT timestamp, current_price AS last_price, volume, high_price, low_price, open_price
                FROM stock_data 
                WHERE symbol = $1 
                AND timestamp >= $2
                ORDER BY timestamp ASC
            """
            start_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            rows = await self.pg_conn.fetch(query, symbol, start_time)
            
            if not rows:
                raise DataFetchError(f"No data found for symbol {symbol}")
                
            df = pd.DataFrame([dict(r) for r in rows])
            logger.info(f"Columns in DataFrame: {df.columns}")
            logger.info(f"First few rows for {symbol}: {df.head()}")

            # Convert columns to float
            for col in ['last_price', 'volume', 'high_price', 'low_price', 'open_price']:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(float)

            if df[['last_price', 'volume', 'high_price', 'low_price', 'open_price']].isnull().any().any():
                logger.warning(f"NaN values found in numeric columns for {symbol}")
            
            # Validate data
            required_columns = ['timestamp', 'last_price', 'volume', 'high_price', 'low_price', 'open_price']
            if not all(col in df.columns for col in required_columns):
                raise DataFetchError("Missing required columns in data")
                
            return df
            
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            raise DataFetchError(f"Failed to fetch data for {symbol}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise DataFetchError(f"Error processing data for {symbol}")

    async def perform_technical_analysis(self, symbol: str) -> Dict:
        """Perform comprehensive technical analysis"""
        try:
            df = await self.get_historical_data(symbol)
            
            # Lowered minimum required for testing
            if len(df) < 1:
                raise AnalysisError(f"No data points for {symbol}")
            
            # Calculate technical indicators with error handling and window checks
            try:
                if len(df) >= 20:
                    df['SMA_20'] = talib.SMA(df['last_price'], timeperiod=20)
                else:
                    df['SMA_20'] = np.nan

                if len(df) >= 50:
                    df['SMA_50'] = talib.SMA(df['last_price'], timeperiod=50)
                else:
                    df['SMA_50'] = np.nan

                if len(df) >= 14:
                    df['RSI'] = talib.RSI(df['last_price'], timeperiod=14)
                else:
                    df['RSI'] = np.nan

                if len(df) >= 26:
                    macd, macd_signal, _ = talib.MACD(df['last_price'])
                    df['MACD'] = macd
                    df['MACD_SIGNAL'] = macd_signal
                else:
                    df['MACD'] = np.nan
                    df['MACD_SIGNAL'] = np.nan

                if len(df) >= 20:
                    bb_upper, bb_middle, bb_lower = talib.BBANDS(df['last_price'])
                    df['BB_UPPER'] = bb_upper
                    df['BB_MIDDLE'] = bb_middle
                    df['BB_LOWER'] = bb_lower
                else:
                    df['BB_UPPER'] = np.nan
                    df['BB_MIDDLE'] = np.nan
                    df['BB_LOWER'] = np.nan
            except Exception as e:
                logger.error(f"Error calculating indicators: {e}")
                raise AnalysisError("Failed to calculate technical indicators")
            
            # Generate signals with validation
            signals = {
                "trend": self._analyze_trend(df),
                "momentum": self._analyze_momentum(df),
                "volatility": self._analyze_volatility(df),
                "support_levels": self._find_support_levels(df),
                "resistance_levels": self._find_resistance_levels(df),
                "patterns": self._identify_patterns(df)
            }
            
            # Validate signal structure
            self._validate_signals(signals)
            
            return signals
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            raise AnalysisError(f"Technical analysis failed for {symbol}")

    def _validate_signals(self, signals: Dict) -> None:
        """Validate signal structure and values"""
        required_keys = ["trend", "momentum", "volatility", "support_levels", "resistance_levels", "patterns"]
        if not all(key in signals for key in required_keys):
            raise AnalysisError("Missing required signal components")
            
        # Validate trend data
        if not isinstance(signals["trend"], dict):
            raise AnalysisError("Invalid trend data structure")
            
        # Validate momentum data
        if not isinstance(signals["momentum"], dict):
            raise AnalysisError("Invalid momentum data structure")
            
        # Add more validation as needed

    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze price trends"""
        current_price = df['last_price'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        
        return {
            "trend": "bullish" if current_price > sma_20 > sma_50 else "bearish",
            "strength": abs(current_price - sma_20) / sma_20,
            "support_levels": self._find_support_levels(df),
            "resistance_levels": self._find_resistance_levels(df)
        }

    def _analyze_momentum(self, df: pd.DataFrame) -> Dict:
        """Analyze price momentum"""
        rsi = df['RSI'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_SIGNAL'].iloc[-1]
        
        return {
            "rsi_signal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral",
            "macd_signal": "bullish" if macd > macd_signal else "bearish",
            "momentum_strength": abs(macd - macd_signal)
        }

    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """Analyze price volatility"""
        bb_upper = df['BB_UPPER'].iloc[-1]
        bb_lower = df['BB_LOWER'].iloc[-1]
        current_price = df['last_price'].iloc[-1]
        
        return {
            "volatility": (bb_upper - bb_lower) / bb_lower,
            "price_position": (current_price - bb_lower) / (bb_upper - bb_lower),
            "volatility_trend": "increasing" if df['BB_UPPER'].diff().iloc[-1] > 0 else "decreasing"
        }

    async def perform_fundamental_analysis(self, symbol: str) -> Dict:
        """Perform fundamental analysis (stub: returns dummy data if company_data table is missing)"""
        # TEMPORARY: Return dummy data if company_data table is missing
        return {
            "pe_ratio": None,
            "dividend_yield": None,
            "book_value": None,
            "financial_health": "unknown"
        }

    async def analyze_news(self, symbol: str) -> Dict:
        """Analyze news and sentiment"""
        # Search for recent news
        search_query = f"NEPSE {symbol} stock news last 7 days"
        news_results = self.perplexity_search.search(search_query)
        
        # Debug logging for diagnosis
        logger.info(f"news_results type: {type(news_results)}")
        logger.info(f"news_results preview: {str(news_results)[:100]}")
        
        # If news_results is a string, use it directly
        if isinstance(news_results, str):
            news_text = news_results
        else:
            # If it's a list or object, extract text appropriately
            news_text = getattr(news_results, 'content', str(news_results))
        logger.info(f"news_text preview: {news_text[:100]}")
        
        # Always return a dict with a 'content' key to avoid downstream .content errors
        news_dict = {"content": news_text}
        
        # Analyze sentiment
        sentiment_prompt = f"""
        Analyze the sentiment of the following news about {symbol} stock.
        Consider market impact, company performance, and future outlook.
        
        News: {news_text}
        
        Provide analysis in the following format:
        {{
            "overall_sentiment": float,  # -1 to 1
            "key_events": List[str],
            "market_impact": str,
            "future_outlook": str,
            "confidence": float
        }}
        """
        
        response = await self.llm.agenerate([sentiment_prompt])
        sentiment = json.loads(response.generations[0][0].text)
        news_dict.update(sentiment)
        return news_dict

    async def analyze_market_behavior(self, symbol: str) -> Dict:
        """Analyze market behavior and patterns"""
        df = await self.get_historical_data(symbol)
        
        # Analyze volume patterns
        volume_analysis = self._analyze_volume_patterns(df)
        
        # Analyze price patterns
        price_patterns = self._analyze_price_patterns(df)
        
        # Analyze market correlation
        market_correlation = await self._analyze_market_correlation(symbol)
        
        return {
            "volume_analysis": volume_analysis,
            "price_patterns": price_patterns,
            "market_correlation": market_correlation
        }

    async def generate_trading_signal(self, symbol: str) -> Dict:
        """Generate comprehensive trading signal"""
        try:
            # Input validation
            if not symbol:
                raise ValueError("Stock symbol is required")
            # Gather all analyses with error handling
            try:
                technical = await self.perform_technical_analysis(symbol)
                fundamental = await self.perform_fundamental_analysis(symbol)
                news = await self.analyze_news(symbol)
                market = await self.analyze_market_behavior(symbol)
            except Exception as e:
                logger.error(f"Analysis failed: {repr(e)}")
                raise AnalysisError(f"Failed to complete analysis for {symbol}: {repr(e)}")
            # Generate signal with validation
            try:
                signal = await self._generate_signal(symbol, technical, fundamental, news, market)
                self._validate_signal(signal)
                return signal
            except Exception as e:
                logger.error(f"Signal generation failed: {repr(e)}")
                raise AnalysisError(f"Failed to generate signal for {symbol}: {repr(e)}")
        except Exception as e:
            logger.error(f"Trading signal generation failed: {repr(e)}")
            raise TradingAgentError(f"Failed to generate trading signal for {symbol}: {repr(e)}")

    def _validate_signal(self, signal: Dict) -> None:
        """Validate trading signal structure and values"""
        required_fields = [
            "signal", "confidence", "entry_price", "stop_loss",
            "take_profit", "timeframe", "reasoning", "risk_level",
            "validation_factors", "caveats"
        ]
        
        if not all(field in signal for field in required_fields):
            raise AnalysisError("Missing required signal fields")
            
        # Validate signal type
        if signal["signal"] not in ["BUY", "SELL", "HOLD"]:
            raise AnalysisError("Invalid signal type")
            
        # Validate numeric values
        if not (0 <= signal["confidence"] <= 1):
            raise AnalysisError("Invalid confidence value")
            
        if signal["entry_price"] <= 0:
            raise AnalysisError("Invalid entry price")
            
        if signal["stop_loss"] <= 0:
            raise AnalysisError("Invalid stop loss")
            
        if signal["take_profit"] <= 0:
            raise AnalysisError("Invalid take profit")

    async def _generate_signal(self, symbol: str, technical: Dict, fundamental: Dict, news: Dict, market: Dict) -> Dict:
        """Generate trading signal from analyses"""
        try:
            # Defensive: ensure news is a dict with 'content' key
            if not isinstance(news, dict):
                news = {"content": str(news)}
            elif "content" not in news:
                news["content"] = str(news)

            signal_prompt = f"""
            Generate a trading signal based on the following analyses:
            
            Technical Analysis: {json.dumps(technical)}
            Fundamental Analysis: {json.dumps(fundamental)}
            News Analysis: {json.dumps(news)}
            Market Behavior: {json.dumps(market)}
            
            Provide a detailed trading signal in the following format:
            {{
                "signal": str,  # "BUY", "SELL", or "HOLD"
                "confidence": float,  # 0 to 1
                "entry_price": float,
                "stop_loss": float,
                "take_profit": float,
                "timeframe": str,
                "reasoning": str,
                "risk_level": str,
                "validation_factors": List[str],
                "caveats": List[str]
            }}
            """
            
            response = await self.llm.agenerate([signal_prompt])
            signal = json.loads(response.generations[0][0].text)
            
            # Add metadata
            signal.update({
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "analyses": {
                    "technical": technical,
                    "fundamental": fundamental,
                    "news": news,
                    "market": market
                }
            })
            
            return signal
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse signal: {e}")
            raise AnalysisError("Invalid signal format")
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            raise AnalysisError("Failed to generate trading signal")

    def _find_support_levels(self, df: pd.DataFrame) -> list:
        """Find support levels (simple: lowest prices in recent window)"""
        return [df['low_price'].tail(5).min()]

    def _find_resistance_levels(self, df: pd.DataFrame) -> list:
        """Find resistance levels (simple: highest prices in recent window)"""
        return [df['high_price'].tail(5).max()]

    def _identify_patterns(self, df: pd.DataFrame) -> list:
        """Identify chart patterns (placeholder implementation)"""
        return []

class TradingSignalPromptTemplate(StringPromptTemplate):
    template: str
    tools: List[Tool]
    input_variables: List[str] = ["input", "chat_history", "agent_scratchpad", "tools"]
    
    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        
        for action, observation in intermediate_steps:
            thoughts += f"\nAction: {action}\nObservation: {observation}\n"
        
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # chat_history may be supplied via kwargs; default to empty string to avoid attribute errors
        kwargs["chat_history"] = kwargs.get("chat_history", "")
        
        return self.template.format(**kwargs)

async def main():
    # Initialize connections
    pg_conn = await asyncpg.connect(os.getenv("PG_DSN"))
    redis_conn = redis.from_url(os.getenv("REDIS_URL"))
    
    # Create agent
    agent = NepseTradingAgent(pg_conn, redis_conn)
    
    # Generate signals
    result = await agent.generate_trading_signal("NABIL")
    
    # Format and print the result
    print("\nNEPSE TRADING SIGNAL REPORT")
    print("=" * 40)
    print(f"Symbol: {result['symbol']}")
    print(f"Generated: {result['timestamp']}")
    print("\nSIGNAL DETAILS")
    print("-" * 20)
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    print(f"\nEntry Price: Rs. {result['entry_price']:.2f}")
    print(f"Stop Loss: Rs. {result['stop_loss']:.2f}")
    print(f"Take Profit: Rs. {result['take_profit']:.2f}")
    print(f"Timeframe: {result['timeframe']}")
    print(f"Risk Level: {result['risk_level']}")
    
    print("\nREASONING")
    print("-" * 20)
    print(result['reasoning'])
    
    print("\nVALIDATION FACTORS")
    print("-" * 20)
    for factor in result['validation_factors']:
        print(f"- {factor}")
    
    print("\nCAVEATS")
    print("-" * 20)
    for caveat in result['caveats']:
        print(f"- {caveat}")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    asyncio.run(main())