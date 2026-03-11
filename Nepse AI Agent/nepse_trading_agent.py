import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import numpy as np
import pandas as pd
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain.chat_models import ChatOpenAI
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

class NepseTradingAgent:
    def __init__(self, pg_conn, redis_conn):
        if not pg_conn or not redis_conn:
            raise ValueError("Database connections are required")
            
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4")
        self.search = DuckDuckGoSearchRun()
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
                    name="NewsAnalysis",
                    func=self.analyze_news,
                    description="Analyze news and sentiment"
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
                
            df = pd.DataFrame(rows)
            
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
            
            # Validate data before analysis
            if len(df) < 50:  # Minimum required for reliable analysis
                raise AnalysisError(f"Insufficient data points for {symbol}")
            
            # Calculate technical indicators with error handling
            try:
                df['SMA_20'] = talib.SMA(df['last_price'], timeperiod=20)
                df['SMA_50'] = talib.SMA(df['last_price'], timeperiod=50)
                df['RSI'] = talib.RSI(df['last_price'], timeperiod=14)
                df['MACD'], df['MACD_SIGNAL'], _ = talib.MACD(df['last_price'])
                df['BB_UPPER'], df['BB_MIDDLE'], df['BB_LOWER'] = talib.BBANDS(df['last_price'])
            except Exception as e:
                logger.error(f"Error calculating indicators: {e}")
                raise AnalysisError("Failed to calculate technical indicators")
            
            # Generate signals with validation
            signals = {
                "trend": self._analyze_trend(df),
                "momentum": self._analyze_momentum(df),
                "volatility": self._analyze_volatility(df),
                "support_resistance": self._find_support_resistance(df),
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
        required_keys = ["trend", "momentum", "volatility", "support_resistance", "patterns"]
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
        """Perform fundamental analysis"""
        # Fetch company information and financial data
        query = """
            SELECT * FROM company_data 
            WHERE symbol = $1
        """
        company_data = await self.pg_conn.fetchrow(query, symbol)
        
        # Analyze financial ratios and metrics
        analysis = {
            "pe_ratio": self._calculate_pe_ratio(company_data),
            "dividend_yield": self._calculate_dividend_yield(company_data),
            "book_value": self._calculate_book_value(company_data),
            "financial_health": self._assess_financial_health(company_data)
        }
        
        return analysis

    async def analyze_news(self, symbol: str) -> Dict:
        """Analyze news and sentiment"""
        # Search for recent news
        search_query = f"NEPSE {symbol} stock news last 7 days"
        news_results = self.search.run(search_query)
        
        # Analyze sentiment
        sentiment_prompt = f"""
        Analyze the sentiment of the following news about {symbol} stock.
        Consider market impact, company performance, and future outlook.
        
        News: {news_results}
        
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
        return json.loads(response.generations[0][0].text)

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
                logger.error(f"Analysis failed: {e}")
                raise AnalysisError(f"Failed to complete analysis for {symbol}")
            
            # Generate signal with validation
            try:
                signal = await self._generate_signal(symbol, technical, fundamental, news, market)
                self._validate_signal(signal)
                return signal
            except Exception as e:
                logger.error(f"Signal generation failed: {e}")
                raise AnalysisError(f"Failed to generate signal for {symbol}")
                
        except Exception as e:
            logger.error(f"Trading signal generation failed: {e}")
            raise TradingAgentError(f"Failed to generate trading signal for {symbol}")

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