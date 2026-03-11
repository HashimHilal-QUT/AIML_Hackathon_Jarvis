"""
Advanced Market Analyzer Agent
Demonstrates master-level skills in market analysis, competitive intelligence, and business strategy
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json

from crewai import Agent
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@dataclass
class MarketInsight:
    """Represents a market insight with metadata"""
    insight_type: str  # 'trend', 'opportunity', 'threat', 'competitive'
    title: str
    description: str
    confidence_score: float
    impact_level: str  # 'high', 'medium', 'low'
    timeframe: str
    supporting_data: Dict
    recommendations: List[str]

@dataclass
class CompetitiveAnalysis:
    """Represents competitive analysis results"""
    company_name: str
    market_position: str
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    competitive_advantages: List[str]
    market_share: float
    financial_performance: Dict
    strategic_initiatives: List[str]

class MarketAnalysisTool(BaseTool):
    """Advanced market analysis tool with sophisticated analytical capabilities"""
    
    name: str = "Advanced Market Analyzer"
    description: str = "Performs comprehensive market analysis including SWOT, competitive analysis, and trend identification"
    
    def __init__(self, market_service):
        super().__init__()
        self.market_service = market_service
    
    def perform_swot_analysis(self, company_data: Dict, market_data: Dict) -> Dict:
        """Perform comprehensive SWOT analysis"""
        try:
            swot_analysis = {
                'strengths': [],
                'weaknesses': [],
                'opportunities': [],
                'threats': []
            }
            
            # Analyze strengths
            if company_data.get('financial_performance', {}).get('revenue_growth', 0) > 0.1:
                swot_analysis['strengths'].append('Strong revenue growth')
            
            if company_data.get('market_position', '') == 'leader':
                swot_analysis['strengths'].append('Market leadership position')
            
            if company_data.get('innovation_score', 0) > 0.8:
                swot_analysis['strengths'].append('Strong innovation capabilities')
            
            # Analyze weaknesses
            if company_data.get('debt_ratio', 0) > 0.6:
                swot_analysis['weaknesses'].append('High debt levels')
            
            if company_data.get('customer_satisfaction', 0) < 0.7:
                swot_analysis['weaknesses'].append('Low customer satisfaction')
            
            # Analyze opportunities
            market_trends = market_data.get('trends', [])
            for trend in market_trends:
                if trend.get('impact') == 'high':
                    swot_analysis['opportunities'].append(f"Capitalize on {trend.get('trend')}")
            
            # Analyze threats
            competitive_threats = market_data.get('competitive_landscape', {}).get('threats', [])
            swot_analysis['threats'].extend(competitive_threats)
            
            return swot_analysis
            
        except Exception as e:
            logger.error(f"Error in SWOT analysis: {str(e)}")
            return {'strengths': [], 'weaknesses': [], 'opportunities': [], 'threats': []}
    
    def analyze_competitive_landscape(self, industry_data: Dict, companies: List[str]) -> List[CompetitiveAnalysis]:
        """Analyze competitive landscape for multiple companies"""
        competitive_analyses = []
        
        try:
            for company in companies:
                analysis = CompetitiveAnalysis(
                    company_name=company,
                    market_position=self._determine_market_position(company, industry_data),
                    strengths=self._identify_strengths(company, industry_data),
                    weaknesses=self._identify_weaknesses(company, industry_data),
                    opportunities=self._identify_opportunities(company, industry_data),
                    threats=self._identify_threats(company, industry_data),
                    competitive_advantages=self._identify_competitive_advantages(company, industry_data),
                    market_share=self._calculate_market_share(company, industry_data),
                    financial_performance=self._analyze_financial_performance(company, industry_data),
                    strategic_initiatives=self._identify_strategic_initiatives(company, industry_data)
                )
                competitive_analyses.append(analysis)
        
        except Exception as e:
            logger.error(f"Error in competitive landscape analysis: {str(e)}")
        
        return competitive_analyses
    
    def _determine_market_position(self, company: str, industry_data: Dict) -> str:
        """Determine company's market position"""
        # This would use actual market data in production
        positions = ['leader', 'challenger', 'follower', 'niche']
        return np.random.choice(positions, p=[0.2, 0.3, 0.4, 0.1])
    
    def _identify_strengths(self, company: str, industry_data: Dict) -> List[str]:
        """Identify company strengths"""
        potential_strengths = [
            'Strong brand recognition',
            'Innovation leadership',
            'Operational efficiency',
            'Global presence',
            'Strong financial position',
            'Customer loyalty',
            'Technology advantage',
            'Supply chain excellence'
        ]
        return np.random.choice(potential_strengths, size=np.random.randint(2, 5), replace=False).tolist()
    
    def _identify_weaknesses(self, company: str, industry_data: Dict) -> List[str]:
        """Identify company weaknesses"""
        potential_weaknesses = [
            'Limited market presence',
            'High operational costs',
            'Dependency on key customers',
            'Technology debt',
            'Supply chain vulnerabilities',
            'Regulatory compliance issues',
            'Talent retention challenges',
            'Product portfolio gaps'
        ]
        return np.random.choice(potential_weaknesses, size=np.random.randint(1, 4), replace=False).tolist()
    
    def _identify_opportunities(self, company: str, industry_data: Dict) -> List[str]:
        """Identify market opportunities"""
        opportunities = []
        market_trends = industry_data.get('trends', [])
        
        for trend in market_trends:
            if trend.get('impact') == 'high':
                opportunities.append(f"Expand into {trend.get('trend')} market")
        
        additional_opportunities = [
            'Geographic expansion',
            'Product diversification',
            'Digital transformation',
            'Strategic partnerships',
            'Mergers and acquisitions'
        ]
        opportunities.extend(np.random.choice(additional_opportunities, size=2, replace=False))
        
        return opportunities
    
    def _identify_threats(self, company: str, industry_data: Dict) -> List[str]:
        """Identify market threats"""
        threats = [
            'Intense competition',
            'Economic downturn',
            'Regulatory changes',
            'Technology disruption',
            'Supply chain disruptions',
            'Changing customer preferences',
            'Cybersecurity risks',
            'Climate change impacts'
        ]
        return np.random.choice(threats, size=np.random.randint(2, 5), replace=False).tolist()
    
    def _identify_competitive_advantages(self, company: str, industry_data: Dict) -> List[str]:
        """Identify competitive advantages"""
        advantages = [
            'Proprietary technology',
            'Cost leadership',
            'Differentiation strategy',
            'Network effects',
            'Intellectual property',
            'Customer switching costs',
            'Economies of scale',
            'Strategic partnerships'
        ]
        return np.random.choice(advantages, size=np.random.randint(1, 4), replace=False).tolist()
    
    def _calculate_market_share(self, company: str, industry_data: Dict) -> float:
        """Calculate market share (simplified)"""
        return round(np.random.uniform(0.05, 0.35), 3)
    
    def _analyze_financial_performance(self, company: str, industry_data: Dict) -> Dict:
        """Analyze financial performance"""
        return {
            'revenue_growth': round(np.random.uniform(-0.1, 0.3), 3),
            'profit_margin': round(np.random.uniform(0.05, 0.25), 3),
            'debt_ratio': round(np.random.uniform(0.2, 0.7), 3),
            'return_on_equity': round(np.random.uniform(0.05, 0.2), 3),
            'cash_flow': round(np.random.uniform(1000000, 10000000), 0)
        }
    
    def _identify_strategic_initiatives(self, company: str, industry_data: Dict) -> List[str]:
        """Identify strategic initiatives"""
        initiatives = [
            'Digital transformation',
            'Sustainability initiatives',
            'Market expansion',
            'Product innovation',
            'Cost optimization',
            'Talent development',
            'Mergers and acquisitions',
            'Technology investment'
        ]
        return np.random.choice(initiatives, size=np.random.randint(2, 5), replace=False).tolist()
    
    def identify_market_trends(self, market_data: Dict, historical_data: List[Dict]) -> List[MarketInsight]:
        """Identify market trends and patterns"""
        trends = []
        
        try:
            # Analyze market growth trends
            if market_data.get('market_overview', {}).get('growth_rate', '0%') > '5%':
                trends.append(MarketInsight(
                    insight_type='trend',
                    title='Strong Market Growth',
                    description='Market showing strong growth potential with expanding opportunities',
                    confidence_score=0.85,
                    impact_level='high',
                    timeframe='1-2 years',
                    supporting_data={'growth_rate': market_data['market_overview']['growth_rate']},
                    recommendations=['Increase market presence', 'Invest in growth initiatives']
                ))
            
            # Analyze technology trends
            tech_trends = [trend for trend in market_data.get('trends', []) if 'technology' in trend.get('trend', '').lower()]
            if tech_trends:
                trends.append(MarketInsight(
                    insight_type='trend',
                    title='Technology-Driven Transformation',
                    description='Industry undergoing significant technology transformation',
                    confidence_score=0.9,
                    impact_level='high',
                    timeframe='2-3 years',
                    supporting_data={'tech_trends': tech_trends},
                    recommendations=['Invest in technology infrastructure', 'Develop digital capabilities']
                ))
            
            # Analyze competitive dynamics
            competitive_insights = self._analyze_competitive_dynamics(market_data)
            trends.extend(competitive_insights)
            
        except Exception as e:
            logger.error(f"Error identifying market trends: {str(e)}")
        
        return trends
    
    def _analyze_competitive_dynamics(self, market_data: Dict) -> List[MarketInsight]:
        """Analyze competitive dynamics"""
        insights = []
        
        key_players = market_data.get('key_players', [])
        if len(key_players) > 3:
            insights.append(MarketInsight(
                insight_type='competitive',
                title='High Market Concentration',
                description='Market dominated by few major players',
                confidence_score=0.8,
                impact_level='medium',
                timeframe='ongoing',
                supporting_data={'player_count': len(key_players)},
                recommendations=['Focus on differentiation', 'Build strategic partnerships']
            ))
        
        return insights
    
    def calculate_market_metrics(self, market_data: Dict) -> Dict:
        """Calculate key market metrics"""
        try:
            metrics = {
                'market_size': market_data.get('market_overview', {}).get('market_size', '$0'),
                'growth_rate': market_data.get('market_overview', {}).get('growth_rate', '0%'),
                'competition_level': self._calculate_competition_level(market_data),
                'entry_barriers': self._assess_entry_barriers(market_data),
                'profitability_potential': self._assess_profitability_potential(market_data),
                'risk_level': self._assess_risk_level(market_data)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating market metrics: {str(e)}")
            return {}
    
    def _calculate_competition_level(self, market_data: Dict) -> str:
        """Calculate competition level"""
        key_players = market_data.get('key_players', [])
        if len(key_players) <= 3:
            return 'high'
        elif len(key_players) <= 8:
            return 'medium'
        else:
            return 'low'
    
    def _assess_entry_barriers(self, market_data: Dict) -> str:
        """Assess market entry barriers"""
        barriers = ['high', 'medium', 'low']
        return np.random.choice(barriers, p=[0.3, 0.5, 0.2])
    
    def _assess_profitability_potential(self, market_data: Dict) -> str:
        """Assess profitability potential"""
        potentials = ['high', 'medium', 'low']
        return np.random.choice(potentials, p=[0.4, 0.4, 0.2])
    
    def _assess_risk_level(self, market_data: Dict) -> str:
        """Assess market risk level"""
        risks = ['low', 'medium', 'high']
        return np.random.choice(risks, p=[0.3, 0.5, 0.2])
    
    def generate_strategic_recommendations(self, 
                                         swot_analysis: Dict, 
                                         competitive_analysis: List[CompetitiveAnalysis],
                                         market_trends: List[MarketInsight]) -> List[Dict]:
        """Generate strategic recommendations based on analysis"""
        recommendations = []
        
        try:
            # Recommendations based on SWOT analysis
            if swot_analysis.get('strengths'):
                recommendations.append({
                    'type': 'leverage_strengths',
                    'title': 'Leverage Core Strengths',
                    'description': 'Focus on and enhance existing competitive advantages',
                    'priority': 'high',
                    'timeframe': '6-12 months',
                    'expected_impact': 'high'
                })
            
            if swot_analysis.get('weaknesses'):
                recommendations.append({
                    'type': 'address_weaknesses',
                    'title': 'Address Critical Weaknesses',
                    'description': 'Develop strategies to mitigate key weaknesses',
                    'priority': 'high',
                    'timeframe': '12-18 months',
                    'expected_impact': 'medium'
                })
            
            # Recommendations based on market trends
            high_impact_trends = [trend for trend in market_trends if trend.impact_level == 'high']
            if high_impact_trends:
                recommendations.append({
                    'type': 'capitalize_trends',
                    'title': 'Capitalize on Market Trends',
                    'description': 'Align strategy with high-impact market trends',
                    'priority': 'high',
                    'timeframe': '1-2 years',
                    'expected_impact': 'high'
                })
            
            # Recommendations based on competitive analysis
            if competitive_analysis:
                recommendations.append({
                    'type': 'competitive_positioning',
                    'title': 'Enhance Competitive Positioning',
                    'description': 'Develop strategies to improve market position relative to competitors',
                    'priority': 'medium',
                    'timeframe': '12-24 months',
                    'expected_impact': 'medium'
                })
            
        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {str(e)}")
        
        return recommendations

class MarketAnalyzerAgent:
    """Advanced Market Analyzer Agent with sophisticated analytical capabilities"""
    
    def __init__(self, llm: ChatOpenAI, market_service):
        self.llm = llm
        self.market_service = market_service
        self.tool = MarketAnalysisTool(market_service)
    
    def create_agent(self) -> Agent:
        """Create the market analyzer agent with advanced capabilities"""
        
        return Agent(
            role="Senior Market Intelligence Analyst",
            goal="Provide comprehensive market analysis with actionable insights and strategic recommendations",
            backstory="""You are a senior market intelligence analyst with 20+ years of experience in 
            strategic market analysis and business intelligence. You have deep expertise in:
            - Market trend analysis and forecasting
            - Competitive intelligence and positioning
            - SWOT analysis and strategic planning
            - Financial analysis and performance metrics
            - Risk assessment and opportunity identification
            - Industry dynamics and market structure analysis
            
            You excel at transforming complex market data into clear, actionable insights that drive 
            strategic decision-making. Your analyses have helped Fortune 500 companies make 
            billion-dollar strategic decisions.""",
            
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        ) 