"""
Advanced Competitor Monitor Agent
Demonstrates master-level skills in competitive intelligence and monitoring
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass

from crewai import Agent
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@dataclass
class CompetitorActivity:
    """Represents a competitor activity with metadata"""
    activity_type: str  # 'product_launch', 'pricing_change', 'partnership', 'acquisition'
    company: str
    description: str
    impact_level: str  # 'high', 'medium', 'low'
    date: datetime
    confidence_score: float
    strategic_implications: List[str]
    response_recommendations: List[str]

class CompetitorMonitorTool(BaseTool):
    """Advanced competitor monitoring tool with sophisticated tracking capabilities"""
    
    name: str = "Advanced Competitor Monitor"
    description: str = "Monitors competitor activities and provides competitive intelligence insights"
    
    def __init__(self, data_service):
        super().__init__()
        self.data_service = data_service
    
    def monitor_competitor_activities(self, companies: List[str], timeframe_days: int = 30) -> List[CompetitorActivity]:
        """Monitor competitor activities and identify strategic moves"""
        activities = []
        
        try:
            for company in companies:
                company_activities = self._analyze_company_activities(company, timeframe_days)
                activities.extend(company_activities)
            
            # Sort by impact level and date
            activities.sort(key=lambda x: (self._impact_score(x.impact_level), x.date), reverse=True)
            
        except Exception as e:
            logger.error(f"Error monitoring competitor activities: {str(e)}")
        
        return activities
    
    def _analyze_company_activities(self, company: str, timeframe_days: int) -> List[CompetitorActivity]:
        """Analyze activities for a specific company"""
        activities = []
        
        # Simulate different types of activities
        activity_types = [
            'product_launch',
            'pricing_change', 
            'partnership',
            'acquisition',
            'market_expansion',
            'technology_investment',
            'leadership_change',
            'regulatory_filing'
        ]
        
        # Generate 2-5 activities per company
        num_activities = np.random.randint(2, 6)
        
        for i in range(num_activities):
            activity_type = np.random.choice(activity_types)
            activity = self._create_activity(company, activity_type, timeframe_days)
            activities.append(activity)
        
        return activities
    
    def _create_activity(self, company: str, activity_type: str, timeframe_days: int) -> CompetitorActivity:
        """Create a competitor activity with realistic details"""
        
        # Activity descriptions based on type
        descriptions = {
            'product_launch': [
                f'{company} launched new AI-powered product line',
                f'{company} introduced cloud-based solution',
                f'{company} released mobile application',
                f'{company} unveiled enterprise platform'
            ],
            'pricing_change': [
                f'{company} reduced prices by 15%',
                f'{company} introduced premium pricing tier',
                f'{company} launched promotional pricing',
                f'{company} restructured pricing model'
            ],
            'partnership': [
                f'{company} formed strategic partnership with tech giant',
                f'{company} announced distribution agreement',
                f'{company} partnered with startup accelerator',
                f'{company} signed joint venture agreement'
            ],
            'acquisition': [
                f'{company} acquired AI startup for $50M',
                f'{company} purchased competitor division',
                f'{company} bought technology company',
                f'{company} acquired market entry platform'
            ],
            'market_expansion': [
                f'{company} expanded to European market',
                f'{company} entered Asian markets',
                f'{company} launched in emerging markets',
                f'{company} opened new regional offices'
            ],
            'technology_investment': [
                f'{company} invested $100M in R&D',
                f'{company} opened innovation center',
                f'{company} acquired AI patents',
                f'{company} launched technology incubator'
            ],
            'leadership_change': [
                f'{company} appointed new CEO',
                f'{company} hired CTO from competitor',
                f'{company} restructured executive team',
                f'{company} brought in industry veteran'
            ],
            'regulatory_filing': [
                f'{company} filed for new patent',
                f'{company} submitted regulatory approval',
                f'{company} announced compliance initiative',
                f'{company} filed for market authorization'
            ]
        }
        
        description = np.random.choice(descriptions.get(activity_type, [f'{company} made strategic move']))
        impact_level = np.random.choice(['high', 'medium', 'low'], p=[0.2, 0.5, 0.3])
        confidence_score = np.random.uniform(0.7, 0.95)
        
        # Generate date within timeframe
        days_ago = np.random.randint(0, timeframe_days)
        activity_date = datetime.now() - timedelta(days=days_ago)
        
        return CompetitorActivity(
            activity_type=activity_type,
            company=company,
            description=description,
            impact_level=impact_level,
            date=activity_date,
            confidence_score=confidence_score,
            strategic_implications=self._generate_strategic_implications(activity_type, company),
            response_recommendations=self._generate_response_recommendations(activity_type, impact_level)
        )
    
    def _generate_strategic_implications(self, activity_type: str, company: str) -> List[str]:
        """Generate strategic implications for an activity"""
        implications_map = {
            'product_launch': [
                f'{company} is expanding product portfolio',
                'Increased competition in product category',
                'Potential market share shift',
                'Technology advancement in industry'
            ],
            'pricing_change': [
                'Price war may be starting',
                'Market positioning adjustment',
                'Customer acquisition strategy change',
                'Profit margin pressure'
            ],
            'partnership': [
                'Access to new markets or technologies',
                'Enhanced competitive capabilities',
                'Strategic alliance formation',
                'Resource sharing and collaboration'
            ],
            'acquisition': [
                'Market consolidation trend',
                'Technology or talent acquisition',
                'Market entry or expansion',
                'Competitive advantage building'
            ],
            'market_expansion': [
                'Geographic growth strategy',
                'International market entry',
                'Customer base expansion',
                'Revenue diversification'
            ],
            'technology_investment': [
                'Innovation focus increase',
                'Technology leadership positioning',
                'Future capability building',
                'Competitive differentiation'
            ],
            'leadership_change': [
                'Strategic direction change',
                'Management expertise enhancement',
                'Organizational transformation',
                'New vision and priorities'
            ],
            'regulatory_filing': [
                'Compliance and governance focus',
                'Market entry preparation',
                'Intellectual property protection',
                'Regulatory advantage building'
            ]
        }
        
        base_implications = implications_map.get(activity_type, ['Strategic move detected'])
        return np.random.choice(base_implications, size=min(3, len(base_implications)), replace=False).tolist()
    
    def _generate_response_recommendations(self, activity_type: str, impact_level: str) -> List[str]:
        """Generate response recommendations based on activity type and impact"""
        recommendations = []
        
        if impact_level == 'high':
            recommendations.extend([
                'Immediate competitive response required',
                'Strategic review of positioning needed',
                'Accelerate counter-initiative development'
            ])
        
        if activity_type == 'product_launch':
            recommendations.extend([
                'Assess competitive product features',
                'Review pricing strategy',
                'Enhance product differentiation'
            ])
        elif activity_type == 'pricing_change':
            recommendations.extend([
                'Analyze pricing impact on market share',
                'Consider pricing response strategy',
                'Evaluate value proposition'
            ])
        elif activity_type == 'partnership':
            recommendations.extend([
                'Identify potential partnership opportunities',
                'Assess partnership impact on competitive position',
                'Develop counter-partnership strategy'
            ])
        elif activity_type == 'acquisition':
            recommendations.extend([
                'Evaluate acquisition targets',
                'Assess market consolidation opportunities',
                'Strengthen competitive moats'
            ])
        
        return recommendations[:4]  # Limit to 4 recommendations
    
    def _impact_score(self, impact_level: str) -> int:
        """Convert impact level to numeric score for sorting"""
        scores = {'high': 3, 'medium': 2, 'low': 1}
        return scores.get(impact_level, 1)
    
    def analyze_competitive_positioning(self, companies: List[str], market_data: Dict) -> Dict:
        """Analyze competitive positioning of companies"""
        positioning_analysis = {}
        
        try:
            for company in companies:
                positioning = {
                    'market_share': self._estimate_market_share(company),
                    'competitive_advantages': self._identify_competitive_advantages(company),
                    'strategic_focus': self._determine_strategic_focus(company),
                    'threat_level': self._assess_threat_level(company),
                    'response_urgency': self._assess_response_urgency(company)
                }
                positioning_analysis[company] = positioning
            
        except Exception as e:
            logger.error(f"Error analyzing competitive positioning: {str(e)}")
        
        return positioning_analysis
    
    def _estimate_market_share(self, company: str) -> float:
        """Estimate market share for a company"""
        return round(np.random.uniform(0.05, 0.4), 3)
    
    def _identify_competitive_advantages(self, company: str) -> List[str]:
        """Identify competitive advantages for a company"""
        advantages = [
            'Technology leadership',
            'Cost efficiency',
            'Brand recognition',
            'Customer relationships',
            'Distribution network',
            'Intellectual property',
            'Operational excellence',
            'Innovation capability'
        ]
        return np.random.choice(advantages, size=np.random.randint(2, 5), replace=False).tolist()
    
    def _determine_strategic_focus(self, company: str) -> str:
        """Determine strategic focus of a company"""
        focuses = ['innovation', 'cost_leadership', 'differentiation', 'market_expansion', 'consolidation']
        return np.random.choice(focuses)
    
    def _assess_threat_level(self, company: str) -> str:
        """Assess threat level posed by a competitor"""
        threats = ['high', 'medium', 'low']
        return np.random.choice(threats, p=[0.3, 0.5, 0.2])
    
    def _assess_response_urgency(self, company: str) -> str:
        """Assess urgency of response needed"""
        urgencies = ['immediate', 'high', 'medium', 'low']
        return np.random.choice(urgencies, p=[0.2, 0.3, 0.3, 0.2])
    
    def generate_competitive_alerts(self, activities: List[CompetitorActivity]) -> List[Dict]:
        """Generate competitive alerts based on activities"""
        alerts = []
        
        try:
            high_impact_activities = [a for a in activities if a.impact_level == 'high']
            
            for activity in high_impact_activities:
                alert = {
                    'alert_type': 'competitive_move',
                    'severity': 'high' if activity.impact_level == 'high' else 'medium',
                    'title': f'{activity.company} - {activity.activity_type.replace("_", " ").title()}',
                    'description': activity.description,
                    'date': activity.date.isoformat(),
                    'implications': activity.strategic_implications,
                    'recommendations': activity.response_recommendations,
                    'confidence': activity.confidence_score
                }
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error generating competitive alerts: {str(e)}")
        
        return alerts

class CompetitorMonitorAgent:
    """Advanced Competitor Monitor Agent with sophisticated competitive intelligence capabilities"""
    
    def __init__(self, llm: ChatOpenAI, data_service):
        self.llm = llm
        self.data_service = data_service
        self.tool = CompetitorMonitorTool(data_service)
    
    def create_agent(self) -> Agent:
        """Create the competitor monitor agent with advanced capabilities"""
        
        return Agent(
            role="Senior Competitive Intelligence Specialist",
            goal="Monitor competitor activities and provide actionable competitive intelligence insights",
            backstory="""You are a senior competitive intelligence specialist with 18+ years of experience in 
            monitoring and analyzing competitor activities. You have deep expertise in:
            - Real-time competitor activity monitoring
            - Strategic move identification and analysis
            - Competitive positioning assessment
            - Threat and opportunity identification
            - Response strategy development
            - Market dynamics analysis
            
            You excel at identifying early warning signs of competitive moves and providing 
            actionable intelligence that helps organizations stay ahead of the competition. 
            Your insights have prevented millions in potential market share losses.""",
            
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        ) 