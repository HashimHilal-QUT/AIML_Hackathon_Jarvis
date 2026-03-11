"""
Enhanced NEPSE Trading Agent with advanced features
"""

import os
import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import talib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from langchain.agents import Tool, AgentExecutor
from agent_prompts import get_agent_prompt
from fastapi import FastAPI, HTTPException, BackgroundTasks
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketType(Enum):
    NORMAL = "NORMAL"
    CALL = "CALL"
    CIRCUIT = "CIRCUIT"
    HALT = "HALT"

class MarketRegime(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"

@dataclass
class MarketState:
    market_type: MarketType
    regime: MarketRegime
    volatility: float
    liquidity_score: float
    sentiment_score: float
    sector_performance: Dict[str, float]
    market_depth: Dict[str, float]

class NepseEnhancedAgent:
    def __init__(self):
        # Initialize base components
        self.initialize_base_components()
        
        # Initialize advanced components
        self.initialize_advanced_components()
        
        # Initialize market state
        self.market_state = None
        
        # Initialize models
        self.initialize_models()

    def initialize_base_components(self):
        """Initialize basic components"""
        # Market timing
        self.market_hours = {
            "open": "11:00",
            "close": "15:00",
            "pre_open": "10:45",
            "pre_close": "14:45"
        }
        
        # Market parameters
        self.circuit_limit = 0.06  # 6% circuit limit
        self.settlement_days = 3
        self.min_liquidity_threshold = 100000  # NPR
        
        # Initialize agents
        self.initialize_agents()

    def initialize_advanced_components(self):
        """Initialize advanced analysis components"""
        # Technical Analysis
        self.technical_indicators = {
            "trend": ["SMA", "EMA", "MACD", "ADX"],
            "momentum": ["RSI", "Stochastic", "CCI", "ROC"],
            "volatility": ["Bollinger Bands", "ATR", "Keltner Channels"],
            "volume": ["OBV", "Volume SMA", "Money Flow Index"],
            "pattern": ["Candlestick Patterns", "Chart Patterns"]
        }
        
        # Fundamental Analysis
        self.fundamental_metrics = {
            "valuation": ["PE", "PB", "PS", "EV/EBITDA"],
            "growth": ["Revenue Growth", "EPS Growth", "Dividend Growth"],
            "profitability": ["ROE", "ROA", "Operating Margin"],
            "efficiency": ["Asset Turnover", "Inventory Turnover"],
            "liquidity": ["Current Ratio", "Quick Ratio", "Cash Ratio"]
        }
        
        # Market Microstructure
        self.microstructure_metrics = {
            "liquidity": ["Bid-Ask Spread", "Market Depth", "Trading Volume"],
            "order_flow": ["Order Imbalance", "Trade Flow", "Market Impact"],
            "volatility": ["Realized Volatility", "Implied Volatility"],
            "correlation": ["Stock Correlation", "Sector Correlation"]
        }

    def initialize_models(self):
        """Initialize machine learning models"""
        # Market Regime Detection
        self.regime_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Price Prediction
        self.price_model = tf.keras.Sequential([
            tf.keras.layers.LSTM(50, return_sequences=True),
            tf.keras.layers.LSTM(50),
            tf.keras.layers.Dense(1)
        ])
        
        # Sentiment Analysis
        self.sentiment_model = tf.keras.Sequential([
            tf.keras.layers.Embedding(10000, 128),
            tf.keras.layers.LSTM(64),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

    async def analyze_market_state(self) -> MarketState:
        """Analyze current market state"""
        try:
            # Get market data
            market_data = await self._get_market_data()
            
            # Determine market type
            market_type = self._determine_market_type(market_data)
            
            # Detect market regime
            regime = await self._detect_market_regime(market_data)
            
            # Calculate volatility
            volatility = self._calculate_volatility(market_data)
            
            # Assess liquidity
            liquidity_score = await self._assess_market_liquidity()
            
            # Analyze sentiment
            sentiment_score = await self._analyze_market_sentiment()
            
            # Get sector performance
            sector_performance = await self._get_sector_performance()
            
            # Analyze market depth
            market_depth = await self._analyze_market_depth()
            
            return MarketState(
                market_type=market_type,
                regime=regime,
                volatility=volatility,
                liquidity_score=liquidity_score,
                sentiment_score=sentiment_score,
                sector_performance=sector_performance,
                market_depth=market_depth
            )
        except Exception as e:
            logger.error(f"Error analyzing market state: {e}")
            raise

    async def generate_enhanced_signals(self, symbol: str) -> Dict:
        """Generate enhanced trading signals"""
        try:
            # Get market state
            market_state = await self.analyze_market_state()
            
            # Get stock data
            stock_data = await self._get_stock_data(symbol)
            
            # Perform comprehensive analysis
            analysis = await self._perform_comprehensive_analysis(symbol, stock_data, market_state)
            
            # Generate signals
            signals = await self._generate_signals(analysis, market_state)
            
            # Validate signals
            validated_signals = await self._validate_signals(signals, market_state)
            
            return {
                "symbol": symbol,
                "market_state": market_state.__dict__,
                "analysis": analysis,
                "signals": validated_signals,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating enhanced signals: {e}")
            raise

    async def _perform_comprehensive_analysis(self, symbol: str, stock_data: Dict, market_state: MarketState) -> Dict:
        """Perform comprehensive stock analysis"""
        try:
            # Technical Analysis
            technical_analysis = await self._perform_technical_analysis(stock_data)
            
            # Fundamental Analysis
            fundamental_analysis = await self._perform_fundamental_analysis(symbol)
            
            # Market Microstructure Analysis
            microstructure_analysis = await self._analyze_microstructure(symbol, stock_data)
            
            # Sentiment Analysis
            sentiment_analysis = await self._analyze_sentiment(symbol)
            
            # Risk Analysis
            risk_analysis = await self._analyze_risk(symbol, stock_data, market_state)
            
            return {
                "technical": technical_analysis,
                "fundamental": fundamental_analysis,
                "microstructure": microstructure_analysis,
                "sentiment": sentiment_analysis,
                "risk": risk_analysis
            }
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise

    async def _generate_signals(self, analysis: Dict, market_state: MarketState) -> Dict:
        """Generate trading signals based on analysis"""
        try:
            # Combine all analysis components
            combined_score = self._combine_analysis_scores(analysis)
            
            # Generate entry/exit points
            entry_exit = self._generate_entry_exit_points(combined_score, market_state)
            
            # Calculate position size
            position_size = self._calculate_position_size(combined_score, market_state)
            
            # Set risk parameters
            risk_params = self._set_risk_parameters(combined_score, market_state)
            
            return {
                "score": combined_score,
                "entry_exit": entry_exit,
                "position_size": position_size,
                "risk_params": risk_params,
                "confidence": self._calculate_confidence(combined_score, market_state)
            }
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise

    async def _validate_signals(self, signals: Dict, market_state: MarketState) -> Dict:
        """Validate trading signals"""
        try:
            # Check market conditions
            if not self._check_market_conditions(market_state):
                return {"valid": False, "reason": "Unfavorable market conditions"}
            
            # Validate signal strength
            if not self._validate_signal_strength(signals):
                return {"valid": False, "reason": "Weak signal strength"}
            
            # Check risk parameters
            if not self._validate_risk_parameters(signals):
                return {"valid": False, "reason": "Risk parameters exceeded"}
            
            # Validate position size
            if not self._validate_position_size(signals):
                return {"valid": False, "reason": "Position size too large"}
            
            return {
                "valid": True,
                "signals": signals,
                "validation_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error validating signals: {e}")
            raise

    def _combine_analysis_scores(self, analysis: Dict) -> float:
        """Combine different analysis scores"""
        weights = {
            "technical": 0.3,
            "fundamental": 0.3,
            "microstructure": 0.2,
            "sentiment": 0.1,
            "risk": 0.1
        }
        
        return sum(
            analysis[component]["score"] * weight
            for component, weight in weights.items()
        )

    def _generate_entry_exit_points(self, score: float, market_state: MarketState) -> Dict:
        """Generate entry and exit points"""
        # Implementation depends on market state and score
        pass

    def _calculate_position_size(self, score: float, market_state: MarketState) -> float:
        """Calculate position size based on risk and market conditions"""
        # Implementation depends on risk parameters and market state
        pass

    def _set_risk_parameters(self, score: float, market_state: MarketState) -> Dict:
        """Set risk parameters for the trade"""
        # Implementation depends on market state and score
        pass

    def _calculate_confidence(self, score: float, market_state: MarketState) -> float:
        """Calculate confidence level for the signal"""
        # Implementation depends on score and market state
        pass

    def _check_market_conditions(self, market_state: MarketState) -> bool:
        """Check if market conditions are favorable"""
        # Implementation depends on market state
        pass

    def _validate_signal_strength(self, signals: Dict) -> bool:
        """Validate signal strength"""
        # Implementation depends on signal parameters
        pass

    def _validate_risk_parameters(self, signals: Dict) -> bool:
        """Validate risk parameters"""
        # Implementation depends on risk parameters
        pass

    def _validate_position_size(self, signals: Dict) -> bool:
        """Validate position size"""
        # Implementation depends on position size parameters
        pass

    async def generate_daily_report(self) -> Dict:
        """Generate comprehensive daily market report"""
        try:
            # Get market state
            market_state = await self.analyze_market_state()
            
            # Get all stock analyses
            all_stocks = await self._get_all_stocks()
            stock_analyses = []
            
            for symbol in all_stocks:
                try:
                    analysis = await self.generate_enhanced_signals(symbol)
                    stock_analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
            
            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "market_summary": {
                    "market_state": market_state.__dict__,
                    "trading_day": datetime.now().strftime("%Y-%m-%d"),
                    "market_hours": self.market_hours,
                    "settlement_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                },
                "top_gainers": self._get_top_gainers(stock_analyses),
                "top_losers": self._get_top_losers(stock_analyses),
                "high_volume": self._get_high_volume_stocks(stock_analyses),
                "trading_signals": self._get_trading_signals(stock_analyses),
                "sector_analysis": self._get_sector_analysis(stock_analyses),
                "market_insights": self._generate_market_insights(market_state, stock_analyses),
                "risk_assessment": self._generate_risk_assessment(market_state, stock_analyses)
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
            raise

    def _get_top_gainers(self, analyses: List[Dict]) -> List[Dict]:
        """Get top gaining stocks"""
        return sorted(
            [a for a in analyses if a["analysis"]["technical"]["momentum"]["rsi"] > 50],
            key=lambda x: x["analysis"]["technical"]["momentum"]["rsi"],
            reverse=True
        )[:5]

    def _get_top_losers(self, analyses: List[Dict]) -> List[Dict]:
        """Get top losing stocks"""
        return sorted(
            [a for a in analyses if a["analysis"]["technical"]["momentum"]["rsi"] < 50],
            key=lambda x: x["analysis"]["technical"]["momentum"]["rsi"]
        )[:5]

    def _get_high_volume_stocks(self, analyses: List[Dict]) -> List[Dict]:
        """Get stocks with high trading volume"""
        return sorted(
            analyses,
            key=lambda x: x["analysis"]["microstructure"]["liquidity"]["trading_volume"],
            reverse=True
        )[:5]

    def _get_trading_signals(self, analyses: List[Dict]) -> Dict:
        """Get all trading signals"""
        return {
            "buy_signals": [
                a for a in analyses 
                if a["signals"]["valid"] and a["signals"]["signals"]["score"] > 0.7
            ],
            "sell_signals": [
                a for a in analyses 
                if a["signals"]["valid"] and a["signals"]["signals"]["score"] < 0.3
            ],
            "hold_signals": [
                a for a in analyses 
                if a["signals"]["valid"] and 0.3 <= a["signals"]["signals"]["score"] <= 0.7
            ]
        }

    def _get_sector_analysis(self, analyses: List[Dict]) -> Dict:
        """Get sector-wise analysis"""
        sectors = {}
        for analysis in analyses:
            sector = analysis.get("sector", "others")
            if sector not in sectors:
                sectors[sector] = {
                    "stocks": [],
                    "performance": 0.0,
                    "volume": 0.0,
                    "sentiment": 0.0
                }
            sectors[sector]["stocks"].append(analysis)
            sectors[sector]["performance"] += analysis["analysis"]["technical"]["momentum"]["rsi"]
            sectors[sector]["volume"] += analysis["analysis"]["microstructure"]["liquidity"]["trading_volume"]
            sectors[sector]["sentiment"] += analysis["analysis"]["sentiment"]["news_sentiment"]
        
        # Normalize sector metrics
        for sector in sectors:
            count = len(sectors[sector]["stocks"])
            sectors[sector]["performance"] /= count
            sectors[sector]["sentiment"] /= count
        
        return sectors

    def _generate_market_insights(self, market_state: MarketState, analyses: List[Dict]) -> Dict:
        """Generate market insights"""
        return {
            "market_trend": market_state.regime.value,
            "volatility_outlook": "High" if market_state.volatility > 0.02 else "Low",
            "liquidity_conditions": "Good" if market_state.liquidity_score > 0.7 else "Poor",
            "sentiment_summary": "Positive" if market_state.sentiment_score > 0.6 else "Negative",
            "key_observations": self._generate_key_observations(market_state, analyses)
        }

    def _generate_risk_assessment(self, market_state: MarketState, analyses: List[Dict]) -> Dict:
        """Generate risk assessment"""
        return {
            "market_risk": "High" if market_state.volatility > 0.02 else "Low",
            "liquidity_risk": "High" if market_state.liquidity_score < 0.5 else "Low",
            "sector_risks": self._get_sector_risks(analyses),
            "risk_recommendations": self._generate_risk_recommendations(market_state, analyses)
        }

    def _generate_key_observations(self, market_state: MarketState, analyses: List[Dict]) -> List[str]:
        """Generate key market observations"""
        observations = []
        
        # Market regime observation
        observations.append(f"Market is in {market_state.regime.value} regime")
        
        # Volatility observation
        if market_state.volatility > 0.02:
            observations.append("High market volatility observed")
        
        # Liquidity observation
        if market_state.liquidity_score < 0.5:
            observations.append("Low market liquidity conditions")
        
        # Sector performance
        top_sector = max(market_state.sector_performance.items(), key=lambda x: x[1])
        observations.append(f"Strong performance in {top_sector[0]} sector")
        
        return observations

    def _get_sector_risks(self, analyses: List[Dict]) -> Dict:
        """Get sector-wise risk assessment"""
        sector_risks = {}
        for analysis in analyses:
            sector = analysis.get("sector", "others")
            if sector not in sector_risks:
                sector_risks[sector] = {
                    "risk_score": 0.0,
                    "volatility": 0.0,
                    "liquidity": 0.0
                }
            
            sector_risks[sector]["risk_score"] += analysis["analysis"]["risk"]["volatility_risk"]
            sector_risks[sector]["volatility"] += analysis["analysis"]["technical"]["volatility"]["atr"]
            sector_risks[sector]["liquidity"] += analysis["analysis"]["microstructure"]["liquidity"]["market_depth"]
        
        # Normalize sector risks
        for sector in sector_risks:
            count = len([a for a in analyses if a.get("sector") == sector])
            sector_risks[sector]["risk_score"] /= count
            sector_risks[sector]["volatility"] /= count
            sector_risks[sector]["liquidity"] /= count
        
        return sector_risks

    def _generate_risk_recommendations(self, market_state: MarketState, analyses: List[Dict]) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        # Market risk recommendations
        if market_state.volatility > 0.02:
            recommendations.append("Consider reducing position sizes due to high market volatility")
        
        # Liquidity risk recommendations
        if market_state.liquidity_score < 0.5:
            recommendations.append("Exercise caution with large positions due to low liquidity")
        
        # Settlement risk recommendations
        recommendations.append("Remember T+3 settlement period when planning trades")
        
        return recommendations

# Create FastAPI app
app = FastAPI(title="NEPSE Enhanced Trading Agent")

@app.get("/analysis/all")
async def get_all_analysis():
    """Get analysis for all stocks"""
    agent = NepseEnhancedAgent()
    return await agent.generate_daily_report()

@app.get("/analysis/stock/{symbol}")
async def get_stock_analysis(symbol: str):
    """Get analysis for a specific stock"""
    agent = NepseEnhancedAgent()
    return await agent.generate_enhanced_signals(symbol)

@app.get("/analysis/daily-report")
async def get_daily_report():
    """Get comprehensive daily market report"""
    agent = NepseEnhancedAgent()
    return await agent.generate_daily_report()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 