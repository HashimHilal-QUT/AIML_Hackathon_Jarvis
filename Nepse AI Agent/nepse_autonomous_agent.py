import asyncio
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
import logging
from fastapi import FastAPI, BackgroundTasks
import uvicorn
from nepse_trading_agent import NepseTradingAgent
from nepse_news_agent import DeepResearchAgent
import redis.asyncio as redis
import asyncpg
from tabulate import tabulate
import schedule
import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.prompts import StringPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import OpenAI
from agent_prompts import get_agent_prompt
from functools import wraps
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nepse_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_stock_symbol(func):
    """Decorator to validate stock symbols"""
    @wraps(func)
    async def wrapper(self, symbol: str, *args, **kwargs):
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Stock symbol must be a non-empty string")
        
        # NEPSE stock symbol format validation
        if not re.match(r'^[A-Z]{2,5}$', symbol):
            raise ValueError("Invalid stock symbol format")
            
        return await func(self, symbol, *args, **kwargs)
    return wrapper

def rate_limit(calls: int, period: int):
    """Decorator to implement rate limiting"""
    def decorator(func):
        last_reset = time.time()
        calls_made = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_reset, calls_made
            
            current_time = time.time()
            if current_time - last_reset >= period:
                last_reset = current_time
                calls_made = 0
                
            if calls_made >= calls:
                raise Exception(f"Rate limit exceeded. Maximum {calls} calls per {period} seconds")
                
            calls_made += 1
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class NepseAutonomousAgent:
    def __init__(self):
        # Initialize system prompts
        self.autonomous_prompt = get_agent_prompt("autonomous")
        self.trading_prompt = get_agent_prompt("trading")
        self.research_prompt = get_agent_prompt("research")
        self.market_prompt = get_agent_prompt("market")
        
        # Initialize agents with their respective prompts
        self.initialize_agents()
        
        self.pg_conn = None
        self.redis_conn = None
        self.signals_cache = {}
        self.daily_report = {}
        self.last_update = None
        self.is_running = False
        self.market_hours = {
            "open": "11:00",  # NEPSE opens at 11:00 AM
            "close": "15:00",  # NEPSE closes at 3:00 PM
            "pre_open": "10:45",  # Pre-open session
            "pre_close": "14:45"  # Pre-close session
        }
        self.market_days = [0, 1, 2, 3, 4]  # Monday to Friday
        self.settlement_days = 3  # T+3 settlement in Nepal
        self.min_liquidity_threshold = 100000  # Minimum daily turnover in NPR
        self.historical_lookback_days = 60  # 2 months of historical data
        
        # Add rate limiting configuration
        self.rate_limits = {
            "market_data": {"calls": 100, "period": 60},  # 100 calls per minute
            "trading_signal": {"calls": 50, "period": 60},  # 50 calls per minute
            "research": {"calls": 30, "period": 60},  # 30 calls per minute
        }
        
        # Add error tracking
        self.error_counts = {
            "data_fetch": 0,
            "analysis": 0,
            "signal_generation": 0,
            "research": 0
        }
        
        # Add maximum retry attempts
        self.max_retries = 3

    def initialize_agents(self):
        """Initialize all agents with their system prompts"""
        try:
            # Initialize Autonomous Agent
            self.autonomous_agent = self._create_agent(
                prompt=self.autonomous_prompt,
                tools=self._get_autonomous_tools()
            )
            
            # Initialize Trading Signal Agent
            self.trading_agent = self._create_agent(
                prompt=self.trading_prompt,
                tools=self._get_trading_tools()
            )
            
            # Initialize Research Agent
            self.research_agent = self._create_agent(
                prompt=self.research_prompt,
                tools=self._get_research_tools()
            )
            
            # Initialize Market Analysis Agent
            self.market_agent = self._create_agent(
                prompt=self.market_prompt,
                tools=self._get_market_tools()
            )
            
            logger.info("All agents initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    def _create_agent(self, prompt: str, tools: List[Tool]) -> AgentExecutor:
        """Create an agent with the given prompt and tools"""
        try:
            llm = OpenAI(temperature=0)
            agent = LLMSingleActionAgent(
                llm_chain=LLMChain(llm=llm, prompt=StringPromptTemplate.from_template(prompt)),
                allowed_tools=[tool.name for tool in tools],
                stop=["\nObservation:"],
                memory=ConversationBufferMemory(memory_key="chat_history")
            )
            return AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=tools,
                verbose=True,
                memory=ConversationBufferMemory(memory_key="chat_history")
            )
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise

    def _get_autonomous_tools(self) -> List[Tool]:
        """Get tools for autonomous agent"""
        return [
            Tool(
                name="analyze_stock",
                func=self.analyze_stock,
                description="Analyze a specific stock comprehensively"
            ),
            Tool(
                name="generate_daily_report",
                func=self.generate_daily_report,
                description="Generate daily market report"
            ),
            # ... add more tools as needed
        ]

    def _get_trading_tools(self) -> List[Tool]:
        """Get tools for trading signal agent"""
        return [
            Tool(
                name="generate_trading_signal",
                func=self._generate_trading_signal,
                description="Generate trading signal for a stock"
            ),
            # ... add more tools as needed
        ]

    def _get_research_tools(self) -> List[Tool]:
        """Get tools for research agent"""
        return [
            Tool(
                name="analyze_news",
                func=self._analyze_news,
                description="Analyze news and market impact"
            ),
            # ... add more tools as needed
        ]

    def _get_market_tools(self) -> List[Tool]:
        """Get tools for market analysis agent"""
        return [
            Tool(
                name="analyze_market_trends",
                func=self._analyze_market_trends,
                description="Analyze market trends and patterns"
            ),
            # ... add more tools as needed
        ]

    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize database connections
            self.pg_conn = await asyncpg.connect(os.getenv('PG_DSN'))
            self.redis_conn = redis.from_url(os.getenv('REDIS_URL'))
            
            # Create necessary tables
            await self._create_tables()
            
            logger.info("Autonomous agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def _create_tables(self):
        """Create necessary database tables"""
        await self.pg_conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_signals (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                stock_symbol VARCHAR(20),
                current_price DECIMAL(10,2),
                buy_signal BOOLEAN,
                suggested_buy_price DECIMAL(10,2),
                suggested_sell_price DECIMAL(10,2),
                holding_period VARCHAR(20),
                sentiment_score DECIMAL(5,2),
                technical_summary TEXT,
                fundamental_summary TEXT,
                final_signal VARCHAR(10),
                profit_probability DECIMAL(5,2),
                recommended_amount DECIMAL(10,2),
                confidence_score DECIMAL(5,2),
                risk_level VARCHAR(20),
                validation_factors JSONB,
                caveats JSONB,
                market_correlation DECIMAL(5,2),
                volume_analysis JSONB,
                news_sentiment JSONB
            );
            
            CREATE TABLE IF NOT EXISTS daily_reports (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP,
                report_date DATE,
                market_summary TEXT,
                top_picks JSONB,
                risk_analysis JSONB,
                market_trend VARCHAR(20),
                sector_performance JSONB,
                recommendations JSONB
            );
        """)

    @validate_stock_symbol
    @rate_limit(calls=50, period=60)
    async def analyze_stock(self, symbol: str) -> Dict:
        """Analyze a specific stock with validation and rate limiting"""
        try:
            # Get trading signal
            signal = await self.trading_agent.generate_trading_signal(symbol)
            
            # Get news and sentiment
            news = await self.research_agent.get_stock_news(symbol)
            
            # Get historical data for analysis
            historical_data = await self._get_historical_data(symbol)
            
            # Perform comprehensive analysis
            technical_analysis = self._perform_technical_analysis(historical_data)
            fundamental_analysis = await self._perform_fundamental_analysis(symbol)
            market_analysis = self._perform_market_analysis(historical_data)
            news_analysis = self._analyze_news(news)
            
            # Calculate sentiment score
            sentiment_score = self._calculate_sentiment_score(news)
            
            # Generate entry/exit points
            entry_exit_points = self._generate_entry_exit_points(
                historical_data,
                technical_analysis,
                market_analysis
            )
            
            # Identify long-term opportunities
            long_term_analysis = self._analyze_long_term_opportunity(
                historical_data,
                fundamental_analysis,
                news_analysis
            )
            
            # Generate comprehensive analysis
            analysis = {
                "stock_symbol": symbol,
                "current_price": signal.get("entry_price", 0),
                "buy_signal": signal.get("signal") == "BUY",
                "suggested_buy_price": entry_exit_points["entry_price"],
                "suggested_sell_price": entry_exit_points["exit_price"],
                "entry_time": entry_exit_points["entry_time"],
                "exit_time": entry_exit_points["exit_time"],
                "holding_period": signal.get("timeframe", "1D"),
                "sentiment_score": sentiment_score,
                "technical_analysis": {
                    "summary": self._summarize_technical(signal),
                    "indicators": technical_analysis,
                    "patterns": self._identify_patterns(historical_data),
                    "support_resistance": self._find_support_resistance(historical_data),
                    "volume_analysis": self._analyze_volume(historical_data),
                    "momentum_indicators": self._calculate_momentum(historical_data),
                    "trend_analysis": self._analyze_trend(historical_data),
                    "volatility_analysis": self._analyze_volatility(historical_data)
                },
                "fundamental_analysis": {
                    "summary": self._summarize_fundamental(signal),
                    "metrics": fundamental_analysis,
                    "financial_health": self._assess_financial_health(fundamental_analysis),
                    "growth_potential": self._assess_growth_potential(fundamental_analysis),
                    "valuation_metrics": self._calculate_valuation_metrics(fundamental_analysis),
                    "dividend_analysis": self._analyze_dividend(fundamental_analysis),
                    "sector_comparison": self._compare_sector_metrics(fundamental_analysis)
                },
                "market_analysis": {
                    "summary": market_analysis["summary"],
                    "correlation": market_analysis["correlation"],
                    "sector_performance": market_analysis["sector_performance"],
                    "market_trend": market_analysis["market_trend"],
                    "volume_profile": market_analysis["volume_profile"],
                    "market_depth": market_analysis["market_depth"],
                    "liquidity_analysis": market_analysis["liquidity_analysis"]
                },
                "news_analysis": {
                    "summary": news_analysis["summary"],
                    "sentiment": news_analysis["sentiment"],
                    "key_events": news_analysis["key_events"],
                    "impact_analysis": news_analysis["impact_analysis"],
                    "sector_news": news_analysis["sector_news"],
                    "market_sentiment": news_analysis["market_sentiment"]
                },
                "final_signal": signal.get("signal", "WAIT"),
                "profit_probability": signal.get("confidence", 0) * 100,
                "recommended_amount": self._calculate_investment_amount(signal),
                "confidence_score": signal.get("confidence", 0),
                "risk_level": signal.get("risk_level", "MODERATE"),
                "validation_factors": signal.get("validation_factors", []),
                "caveats": signal.get("caveats", []),
                "long_term_opportunity": long_term_analysis,
                "risk_assessment": self._assess_risk(
                    technical_analysis,
                    fundamental_analysis,
                    market_analysis,
                    news_analysis
                ),
                "position_sizing": self._calculate_position_size(
                    signal,
                    technical_analysis,
                    fundamental_analysis
                ),
                "trade_management": {
                    "stop_loss": entry_exit_points["stop_loss"],
                    "take_profit": entry_exit_points["take_profit"],
                    "trailing_stop": entry_exit_points["trailing_stop"],
                    "position_scaling": entry_exit_points["position_scaling"]
                }
            }
            
            # Store in database
            await self._store_signal(analysis)
            
            return analysis
            
        except Exception as e:
            self.error_counts["analysis"] += 1
            logger.error(f"Error analyzing stock {symbol}: {e}")
            raise

    def _calculate_sentiment_score(self, news: List[Dict]) -> float:
        """Calculate overall sentiment score from news"""
        if not news:
            return 0.5  # Neutral if no news
            
        scores = []
        for item in news:
            if item.get("sentiment") == "POSITIVE":
                scores.append(1.0)
            elif item.get("sentiment") == "NEGATIVE":
                scores.append(0.0)
            else:
                scores.append(0.5)
                
        return sum(scores) / len(scores)

    def _summarize_technical(self, signal: Dict) -> str:
        """Summarize technical analysis"""
        tech = signal.get("analyses", {}).get("technical", {})
        return f"Trend: {tech.get('trend', 'NEUTRAL')}, " \
               f"Momentum: {tech.get('momentum', 'NEUTRAL')}, " \
               f"Volatility: {tech.get('volatility', 'MODERATE')}"

    def _summarize_fundamental(self, signal: Dict) -> str:
        """Summarize fundamental analysis"""
        fund = signal.get("analyses", {}).get("fundamental", {})
        return f"P/E: {fund.get('pe_ratio', 'N/A')}, " \
               f"Market Cap: {fund.get('market_cap', 'N/A')}, " \
               f"Dividend Yield: {fund.get('dividend_yield', 'N/A')}%"

    def _calculate_investment_amount(self, signal: Dict) -> float:
        """Calculate recommended investment amount based on risk and confidence"""
        base_amount = 100000  # Base investment amount
        confidence = signal.get("confidence", 0.5)
        risk_level = signal.get("risk_level", "MODERATE")
        
        risk_multiplier = {
            "LOW": 1.0,
            "MODERATE": 0.7,
            "HIGH": 0.4
        }.get(risk_level, 0.7)
        
        return base_amount * confidence * risk_multiplier

    async def _store_signal(self, analysis: Dict):
        """Store analysis in database"""
        try:
            await self.pg_conn.execute("""
                INSERT INTO daily_signals (
                    timestamp, stock_symbol, current_price, buy_signal,
                    suggested_buy_price, suggested_sell_price, holding_period,
                    sentiment_score, technical_summary, fundamental_summary,
                    final_signal, profit_probability, recommended_amount,
                    confidence_score, risk_level, validation_factors,
                    caveats, market_correlation, volume_analysis, news_sentiment
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            """, 
            datetime.now(), analysis["stock_symbol"], analysis["current_price"],
            analysis["buy_signal"], analysis["suggested_buy_price"],
            analysis["suggested_sell_price"], analysis["holding_period"],
            analysis["sentiment_score"], analysis["technical_analysis"]["summary"],
            analysis["fundamental_analysis"]["summary"], analysis["final_signal"],
            analysis["profit_probability"], analysis["recommended_amount"],
            analysis["confidence_score"], analysis["risk_level"],
            json.dumps(analysis["validation_factors"]),
            json.dumps(analysis["caveats"]), analysis["market_correlation"],
            json.dumps(analysis["volume_analysis"]),
            json.dumps(analysis["news_sentiment"])
            )
        except Exception as e:
            logger.error(f"Error storing signal: {e}")

    async def generate_daily_report(self):
        """Generate comprehensive daily report"""
        try:
            # Get all signals for today
            signals = await self.pg_conn.fetch("""
                SELECT * FROM daily_signals 
                WHERE DATE(timestamp) = CURRENT_DATE
                ORDER BY confidence_score DESC
            """)
            
            # Analyze market trends
            market_trend = self._analyze_market_trend(signals)
            
            # Generate sector performance
            sector_performance = self._analyze_sector_performance(signals)
            
            # Generate top picks
            top_picks = self._generate_top_picks(signals)
            
            # Generate risk analysis
            risk_analysis = self._analyze_risk(signals)
            
            # Create report
            report = {
                "timestamp": datetime.now(),
                "report_date": datetime.now().date(),
                "market_summary": self._generate_market_summary(signals),
                "top_picks": top_picks,
                "risk_analysis": risk_analysis,
                "market_trend": market_trend,
                "sector_performance": sector_performance,
                "recommendations": self._generate_recommendations(signals)
            }
            
            # Store report
            await self._store_daily_report(report)
            
            # Print report
            self._print_daily_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            return None

    def _analyze_market_trend(self, signals: List[Dict]) -> str:
        """Analyze overall market trend"""
        buy_signals = sum(1 for s in signals if s["final_signal"] == "BUY")
        sell_signals = sum(1 for s in signals if s["final_signal"] == "SELL")
        
        if buy_signals > sell_signals * 1.5:
            return "STRONG_BULLISH"
        elif buy_signals > sell_signals:
            return "BULLISH"
        elif sell_signals > buy_signals * 1.5:
            return "STRONG_BEARISH"
        elif sell_signals > buy_signals:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _analyze_sector_performance(self, signals: List[Dict]) -> Dict:
        """Analyze performance by sector"""
        sectors = {}
        for signal in signals:
            sector = signal.get("sector", "UNKNOWN")
            if sector not in sectors:
                sectors[sector] = {
                    "buy_signals": 0,
                    "sell_signals": 0,
                    "avg_confidence": 0,
                    "total_stocks": 0
                }
            
            sectors[sector]["total_stocks"] += 1
            if signal["final_signal"] == "BUY":
                sectors[sector]["buy_signals"] += 1
            elif signal["final_signal"] == "SELL":
                sectors[sector]["sell_signals"] += 1
            sectors[sector]["avg_confidence"] += signal["confidence_score"]
            
        # Calculate averages
        for sector in sectors:
            sectors[sector]["avg_confidence"] /= sectors[sector]["total_stocks"]
            
        return sectors

    def _generate_top_picks(self, signals: List[Dict]) -> List[Dict]:
        """Generate top stock picks"""
        return sorted(
            signals,
            key=lambda x: (x["confidence_score"], x["profit_probability"]),
            reverse=True
        )[:5]

    def _analyze_risk(self, signals: List[Dict]) -> Dict:
        """Analyze overall market risk"""
        risk_levels = {
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0
        }
        
        for signal in signals:
            risk_levels[signal["risk_level"]] += 1
            
        total = len(signals)
        return {
            level: count/total for level, count in risk_levels.items()
        }

    def _generate_market_summary(self, signals: List[Dict]) -> str:
        """Generate market summary"""
        market_trend = self._analyze_market_trend(signals)
        risk_analysis = self._analyze_risk(signals)
        
        return f"Market is showing {market_trend} trend. " \
               f"Risk levels: {risk_analysis['LOW']*100:.1f}% Low, " \
               f"{risk_analysis['MODERATE']*100:.1f}% Moderate, " \
               f"{risk_analysis['HIGH']*100:.1f}% High."

    def _generate_recommendations(self, signals: List[Dict]) -> List[Dict]:
        """Generate trading recommendations"""
        recommendations = []
        for signal in signals:
            if signal["confidence_score"] > 0.7:  # High confidence signals
                recommendations.append({
                    "stock_symbol": signal["stock_symbol"],
                    "action": signal["final_signal"],
                    "confidence": signal["confidence_score"],
                    "reasoning": f"Strong {signal['technical_analysis']['summary']} with {signal['sentiment_score']*100:.1f}% positive sentiment"
                })
        return recommendations

    async def _store_daily_report(self, report: Dict):
        """Store daily report in database"""
        try:
            await self.pg_conn.execute("""
                INSERT INTO daily_reports (
                    timestamp, report_date, market_summary,
                    top_picks, risk_analysis, market_trend,
                    sector_performance, recommendations
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            report["timestamp"], report["report_date"],
            report["market_summary"], json.dumps(report["top_picks"]),
            json.dumps(report["risk_analysis"]), report["market_trend"],
            json.dumps(report["sector_performance"]),
            json.dumps(report["recommendations"])
            )
        except Exception as e:
            logger.error(f"Error storing daily report: {e}")

    def _print_daily_report(self, report: Dict):
        """Print formatted daily report with comprehensive analysis"""
        print("\n" + "="*100)
        print(f"DAILY TRADING REPORT - {report['report_date']}")
        print("="*100)
        
        print("\nMARKET SUMMARY:")
        print(report["market_summary"])
        
        print("\nTOP PICKS WITH DETAILED ANALYSIS:")
        for pick in report["top_picks"]:
            print("\n" + "-"*80)
            print(f"STOCK: {pick['stock_symbol']}")
            print(f"SIGNAL: {pick['final_signal']} (Confidence: {pick['confidence_score']*100:.1f}%)")
            print(f"CURRENT PRICE: {pick['current_price']}")
            print(f"ENTRY PRICE: {pick['suggested_buy_price']} (Time: {pick['entry_time']})")
            print(f"EXIT PRICE: {pick['suggested_sell_price']} (Time: {pick['exit_time']})")
            print(f"STOP LOSS: {pick['trade_management']['stop_loss']}")
            print(f"TAKE PROFIT: {pick['trade_management']['take_profit']}")
            
            print("\nTECHNICAL ANALYSIS:")
            tech = pick['technical_analysis']
            print(f"Trend: {tech['trend_analysis']['trend']}")
            print(f"Support Levels: {tech['support_resistance']['support']}")
            print(f"Resistance Levels: {tech['support_resistance']['resistance']}")
            print(f"Volume Analysis: {tech['volume_analysis']['summary']}")
            print(f"Patterns Identified: {', '.join(tech['patterns'])}")
            
            print("\nFUNDAMENTAL ANALYSIS:")
            fund = pick['fundamental_analysis']
            print(f"Financial Health: {fund['financial_health']['rating']}")
            print(f"Growth Potential: {fund['growth_potential']['rating']}")
            print(f"Valuation Metrics: {fund['valuation_metrics']['summary']}")
            print(f"Dividend Analysis: {fund['dividend_analysis']['summary']}")
            
            print("\nMARKET ANALYSIS:")
            market = pick['market_analysis']
            print(f"Market Trend: {market['market_trend']}")
            print(f"Sector Performance: {market['sector_performance']}")
            print(f"Liquidity: {market['liquidity_analysis']['summary']}")
            
            print("\nNEWS ANALYSIS:")
            news = pick['news_analysis']
            print(f"Overall Sentiment: {news['sentiment']}")
            print(f"Key Events: {news['key_events']}")
            print(f"Impact Analysis: {news['impact_analysis']}")
            
            if pick['long_term_opportunity']['is_long_term_opportunity']:
                print("\nLONG-TERM OPPORTUNITY:")
                lto = pick['long_term_opportunity']
                print(f"Recommended Holding Period: {lto['recommended_holding_period']}")
                print(f"Expected Returns: {lto['expected_returns']}")
                print(f"Growth Metrics: {lto['growth_metrics']['summary']}")
                print(f"Future Prospects: {lto['future_prospects']['summary']}")
            
            print("\nRISK ASSESSMENT:")
            print(f"Risk Level: {pick['risk_level']}")
            print(f"Risk Factors: {', '.join(pick['risk_assessment']['factors'])}")
            print(f"Position Size: {pick['position_sizing']['recommended_amount']}")
            print(f"Position Scaling: {pick['trade_management']['position_scaling']}")
            
            print("\nVALIDATION FACTORS:")
            for factor in pick['validation_factors']:
                print(f"- {factor}")
            
            print("\nCAVEATS:")
            for caveat in pick['caveats']:
                print(f"- {caveat}")
        
        print("\nSECTOR PERFORMANCE:")
        for sector, perf in report["sector_performance"].items():
            print(f"\n{sector}:")
            print(f"Buy Signals: {perf['buy_signals']}")
            print(f"Sell Signals: {perf['sell_signals']}")
            print(f"Confidence: {perf['avg_confidence']*100:.1f}%")
            print(f"Trend: {perf['trend']}")
            print(f"Volume: {perf['volume_trend']}")
        
        print("\nMARKET RISK ANALYSIS:")
        risk = report["risk_analysis"]
        print(f"Overall Risk Level: {risk['overall_risk']}")
        print(f"Risk Distribution: {risk['risk_distribution']}")
        print(f"Market Volatility: {risk['market_volatility']}")
        print(f"Liquidity Risk: {risk['liquidity_risk']}")
        
        print("\nRECOMMENDATIONS:")
        for rec in report["recommendations"]:
            print(f"\n{rec['stock_symbol']}:")
            print(f"Action: {rec['action']}")
            print(f"Reasoning: {rec['reasoning']}")
            print(f"Time Frame: {rec['time_frame']}")
            print(f"Risk Level: {rec['risk_level']}")
        
        print("\n" + "="*100)

    async def analyze_all_stocks(self) -> List[Dict]:
        """Analyze all NEPSE stocks comprehensively"""
        try:
            # Get all stock symbols
            symbols = await self._get_all_stocks()
            
            # Get market overview
            market_overview = await self._get_market_overview()
            
            # Get historical data for all stocks
            historical_data = await self._get_historical_data_bulk(symbols)
            
            # Analyze each stock
            analyses = []
            for symbol in symbols:
                try:
                    # Get stock-specific data
                    stock_data = historical_data.get(symbol, {})
                    
                    # Check liquidity
                    if not self._check_liquidity(stock_data):
                        logger.info(f"Skipping {symbol} due to low liquidity")
                        continue
                    
                    # Perform analysis
                    analysis = await self.analyze_stock(symbol)
                    if analysis:
                        # Add market context
                        analysis["market_context"] = {
                            "market_trend": market_overview["trend"],
                            "sector_performance": market_overview["sector_performance"],
                            "market_volatility": market_overview["volatility"],
                            "overall_sentiment": market_overview["sentiment"]
                        }
                        
                        # Add settlement information
                        analysis["settlement_info"] = {
                            "settlement_days": self.settlement_days,
                            "estimated_settlement_date": self._calculate_settlement_date(),
                            "liquidity_risk": self._assess_liquidity_risk(stock_data)
                        }
                        
                        # Add historical context
                        analysis["historical_context"] = {
                            "price_trend": self._analyze_price_trend(stock_data),
                            "volume_trend": self._analyze_volume_trend(stock_data),
                            "volatility_history": self._analyze_volatility_history(stock_data),
                            "correlation_history": self._analyze_correlation_history(stock_data)
                        }
                        
                        analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error in bulk analysis: {e}")
            return []

    def _check_liquidity(self, stock_data: Dict) -> bool:
        """Check if stock meets minimum liquidity requirements"""
        try:
            avg_daily_turnover = np.mean([
                day["volume"] * day["last_price"]
                for day in stock_data.get("daily_data", [])
            ])
            return avg_daily_turnover >= self.min_liquidity_threshold
        except Exception:
            return False

    def _calculate_settlement_date(self) -> str:
        """Calculate estimated settlement date considering T+3"""
        settlement = datetime.now()
        days_added = 0
        while days_added < self.settlement_days:
            settlement += timedelta(days=1)
            if settlement.weekday() in self.market_days:
                days_added += 1
        return settlement.strftime("%Y-%m-%d")

    def _assess_liquidity_risk(self, stock_data: Dict) -> Dict:
        """Assess liquidity risk considering NEPSE market conditions"""
        try:
            daily_volumes = [day["volume"] for day in stock_data.get("daily_data", [])]
            avg_volume = np.mean(daily_volumes)
            volume_std = np.std(daily_volumes)
            
            return {
                "risk_level": "HIGH" if volume_std > avg_volume else "MODERATE",
                "avg_daily_volume": avg_volume,
                "volume_volatility": volume_std / avg_volume,
                "liquidity_score": min(1.0, avg_volume / self.min_liquidity_threshold)
            }
        except Exception:
            return {"risk_level": "UNKNOWN", "liquidity_score": 0}

    async def _get_market_overview(self) -> Dict:
        """Get comprehensive market overview"""
        try:
            # Get index data
            index_data = await self._get_index_data()
            
            # Get sector performance
            sector_data = await self._get_sector_performance()
            
            # Get market sentiment
            sentiment = await self._get_market_sentiment()
            
            return {
                "trend": self._analyze_market_trend(index_data),
                "sector_performance": sector_data,
                "volatility": self._calculate_market_volatility(index_data),
                "sentiment": sentiment,
                "trading_activity": self._analyze_trading_activity(),
                "market_depth": self._analyze_market_depth()
            }
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}

    def _analyze_price_trend(self, stock_data: Dict) -> Dict:
        """Analyze price trend over historical period"""
        try:
            prices = [day["last_price"] for day in stock_data.get("daily_data", [])]
            returns = np.diff(prices) / prices[:-1]
            
            return {
                "trend": "BULLISH" if np.mean(returns) > 0 else "BEARISH",
                "volatility": np.std(returns),
                "momentum": np.mean(returns[-5:]),  # Last 5 days
                "support_levels": self._find_support_levels(prices),
                "resistance_levels": self._find_resistance_levels(prices)
            }
        except Exception:
            return {"trend": "UNKNOWN"}

    def _analyze_volume_trend(self, stock_data: Dict) -> Dict:
        """Analyze volume trend over historical period"""
        try:
            volumes = [day["volume"] for day in stock_data.get("daily_data", [])]
            
            return {
                "trend": "INCREASING" if np.mean(volumes[-5:]) > np.mean(volumes[-10:-5]) else "DECREASING",
                "avg_volume": np.mean(volumes),
                "volume_volatility": np.std(volumes) / np.mean(volumes),
                "recent_volume_trend": np.mean(volumes[-5:]) / np.mean(volumes[-10:-5])
            }
        except Exception:
            return {"trend": "UNKNOWN"}

    def _analyze_volatility_history(self, stock_data: Dict) -> Dict:
        """Analyze historical volatility patterns"""
        try:
            prices = [day["last_price"] for day in stock_data.get("daily_data", [])]
            returns = np.diff(prices) / prices[:-1]
            
            return {
                "historical_volatility": np.std(returns) * np.sqrt(252),  # Annualized
                "volatility_trend": "INCREASING" if np.std(returns[-5:]) > np.std(returns[-10:-5]) else "DECREASING",
                "volatility_regime": self._determine_volatility_regime(returns)
            }
        except Exception:
            return {"historical_volatility": 0}

    def _analyze_correlation_history(self, stock_data: Dict) -> Dict:
        """Analyze historical correlation with market"""
        try:
            stock_returns = np.diff([day["last_price"] for day in stock_data.get("daily_data", [])])
            market_returns = np.diff([day["index"] for day in stock_data.get("market_data", [])])
            
            correlation = np.corrcoef(stock_returns, market_returns)[0, 1]
            
            return {
                "market_correlation": correlation,
                "correlation_trend": "INCREASING" if correlation > 0.7 else "DECREASING",
                "beta": self._calculate_beta(stock_returns, market_returns)
            }
        except Exception:
            return {"market_correlation": 0}

    def _determine_volatility_regime(self, returns: np.ndarray) -> str:
        """Determine current volatility regime"""
        try:
            recent_vol = np.std(returns[-5:])
            historical_vol = np.std(returns)
            
            if recent_vol > historical_vol * 1.5:
                return "HIGH_VOLATILITY"
            elif recent_vol < historical_vol * 0.5:
                return "LOW_VOLATILITY"
            else:
                return "NORMAL_VOLATILITY"
        except Exception:
            return "UNKNOWN"

    def _calculate_beta(self, stock_returns: np.ndarray, market_returns: np.ndarray) -> float:
        """Calculate stock beta"""
        try:
            covariance = np.cov(stock_returns, market_returns)[0, 1]
            market_variance = np.var(market_returns)
            return covariance / market_variance
        except Exception:
            return 1.0

    async def run(self):
        """Main run loop with NEPSE market timing"""
        if not await self.initialize():
            logger.error("Failed to initialize agent")
            return
            
        self.is_running = True
        logger.info("Starting autonomous agent...")
        
        while self.is_running:
            try:
                current_time = datetime.now().strftime("%H:%M")
                
                # Check if market is open
                if self._is_market_open():
                    # Get pre-market data
                    if current_time == self.market_hours["pre_open"]:
                        await self._analyze_pre_market()
                    
                    # Regular market analysis
                    if self.market_hours["open"] <= current_time <= self.market_hours["close"]:
                        analyses = await self.analyze_all_stocks()
                        await self._update_signals(analyses)
                    
                    # Post-market analysis
                    if current_time == self.market_hours["pre_close"]:
                        await self._analyze_post_market()
                    
                    # Generate daily report at market close
                    if current_time == self.market_hours["close"]:
                        await self.generate_daily_report()
                
                # Update last update time
                self.last_update = datetime.now()
                
                # Sleep for 1 minute before next update
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)

    def _is_market_open(self) -> bool:
        """Check if NEPSE market is open"""
        now = datetime.now()
        
        # Check if it's a trading day
        if now.weekday() not in self.market_days:
            return False
            
        # Check market hours
        current_time = now.strftime("%H:%M")
        return self.market_hours["pre_open"] <= current_time <= self.market_hours["close"]

    async def _analyze_pre_market(self):
        """Analyze pre-market conditions"""
        try:
            # Get overnight news
            news = await self.research_agent.get_overnight_news()
            
            # Get pre-market indicators
            indicators = await self._get_pre_market_indicators()
            
            # Update market sentiment
            await self._update_market_sentiment(news, indicators)
            
            logger.info("Pre-market analysis completed")
        except Exception as e:
            logger.error(f"Error in pre-market analysis: {e}")

    async def _analyze_post_market(self):
        """Analyze post-market conditions"""
        try:
            # Get daily summary
            summary = await self._get_daily_summary()
            
            # Update historical data
            await self._update_historical_data()
            
            # Generate end-of-day signals
            await self._generate_eod_signals()
            
            logger.info("Post-market analysis completed")
        except Exception as e:
            logger.error(f"Error in post-market analysis: {e}")

    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry an operation with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                await asyncio.sleep(wait_time)

    async def _validate_market_data(self, data: Dict) -> bool:
        """Validate market data structure and values"""
        required_fields = ["last_price", "volume", "high_price", "low_price", "open_price"]
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return False
                    
            # Validate numeric values
            for field in required_fields:
                if not isinstance(data[field], (int, float)) or data[field] < 0:
                    return False
                    
            # Validate price relationships
            if not (data["low_price"] <= data["last_price"] <= data["high_price"]):
                return False
                
            return True
        except Exception:
            return False

    async def _handle_database_error(self, operation: str, error: Exception):
        """Handle database errors with proper logging and recovery"""
        logger.error(f"Database error during {operation}: {error}")
        
        # Check if connection is lost
        if isinstance(error, asyncpg.exceptions.PostgresError):
            try:
                await self.pg_conn.close()
                self.pg_conn = await asyncpg.connect(os.getenv('PG_DSN'))
                logger.info("Database connection reestablished")
            except Exception as e:
                logger.error(f"Failed to reconnect to database: {e}")
                raise

    async def _validate_trading_signal(self, signal: Dict) -> bool:
        """Validate trading signal structure and values"""
        required_fields = [
            "entry_price", "stop_loss", "take_profit", 
            "confidence", "reasoning", "risk_level"
        ]
        
        try:
            # Check required fields
            for field in required_fields:
                if field not in signal:
                    return False
                    
            # Validate numeric values
            for field in ["entry_price", "stop_loss", "take_profit", "confidence"]:
                if not isinstance(signal[field], (int, float)):
                    return False
                    
            # Validate price relationships
            if not (signal["stop_loss"] < signal["entry_price"] < signal["take_profit"]):
                return False
                
            # Validate confidence
            if not (0 <= signal["confidence"] <= 1):
                return False
                
            return True
        except Exception:
            return False

    async def _monitor_error_rates(self):
        """Monitor error rates and take action if thresholds are exceeded"""
        thresholds = {
            "data_fetch": 10,
            "analysis": 5,
            "signal_generation": 5,
            "research": 5
        }
        
        for operation, count in self.error_counts.items():
            if count >= thresholds[operation]:
                logger.warning(f"High error rate detected for {operation}: {count} errors")
                # Implement recovery actions here
                self.error_counts[operation] = 0  # Reset counter

# Create FastAPI app
app = FastAPI(title="NEPSE Autonomous Trading Agent")

# Global agent instance
agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    agent = NepseAutonomousAgent()
    asyncio.create_task(agent.run())

@app.on_event("shutdown")
async def shutdown_event():
    """Stop agent on shutdown"""
    if agent:
        agent.stop()

@app.get("/status")
async def get_status():
    """Get agent status"""
    if not agent:
        return {"status": "not_initialized"}
        
    return {
        "status": "running" if agent.is_running else "stopped",
        "last_update": agent.last_update.isoformat() if agent.last_update else None
    }

@app.get("/signals")
async def get_signals():
    """Get current trading signals"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
        
    try:
        signals = await agent.pg_conn.fetch("""
            SELECT * FROM daily_signals 
            WHERE DATE(timestamp) = CURRENT_DATE
            ORDER BY confidence_score DESC
        """)
        return [dict(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report")
async def get_daily_report():
    """Get latest daily report"""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
        
    try:
        report = await agent.pg_conn.fetchrow("""
            SELECT * FROM daily_reports 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        return dict(report) if report else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 