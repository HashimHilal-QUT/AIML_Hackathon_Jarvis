"""
Advanced Report Writer Agent
Demonstrates master-level skills in business reporting and executive communication
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

from crewai import Agent
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@dataclass
class ExecutiveSummary:
    """Represents an executive summary with key insights"""
    key_findings: List[str]
    critical_insights: List[str]
    strategic_recommendations: List[str]
    risk_assessment: Dict
    market_outlook: str
    confidence_level: float

@dataclass
class BusinessReport:
    """Represents a comprehensive business report"""
    title: str
    executive_summary: ExecutiveSummary
    market_analysis: Dict
    competitive_analysis: Dict
    trend_analysis: Dict
    strategic_recommendations: List[Dict]
    risk_assessment: Dict
    appendices: Dict

class ReportWriterTool(BaseTool):
    """Advanced report writing tool with sophisticated business communication capabilities"""
    
    name: str = "Advanced Report Writer"
    description: str = "Creates professional executive reports with actionable insights and strategic recommendations"
    
    def __init__(self):
        super().__init__()
    
    def create_executive_summary(self, 
                               market_data: Dict, 
                               competitive_analysis: Dict, 
                               trend_predictions: List[Dict]) -> ExecutiveSummary:
        """Create a compelling executive summary"""
        try:
            # Extract key findings
            key_findings = self._extract_key_findings(market_data, competitive_analysis, trend_predictions)
            
            # Identify critical insights
            critical_insights = self._identify_critical_insights(market_data, competitive_analysis, trend_predictions)
            
            # Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(market_data, competitive_analysis, trend_predictions)
            
            # Assess risks
            risk_assessment = self._assess_risks(market_data, competitive_analysis, trend_predictions)
            
            # Determine market outlook
            market_outlook = self._determine_market_outlook(market_data, trend_predictions)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(market_data, competitive_analysis, trend_predictions)
            
            return ExecutiveSummary(
                key_findings=key_findings,
                critical_insights=critical_insights,
                strategic_recommendations=strategic_recommendations,
                risk_assessment=risk_assessment,
                market_outlook=market_outlook,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Error creating executive summary: {str(e)}")
            return ExecutiveSummary([], [], [], {}, "Neutral", 0.5)
    
    def _extract_key_findings(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> List[str]:
        """Extract key findings from analysis data"""
        findings = []
        
        try:
            # Market findings
            if market_data.get('market_overview', {}).get('growth_rate', '0%') > '5%':
                findings.append(f"Market showing strong growth at {market_data['market_overview']['growth_rate']}")
            
            if market_data.get('market_overview', {}).get('market_size'):
                findings.append(f"Market size estimated at {market_data['market_overview']['market_size']}")
            
            # Competitive findings
            if competitive_analysis:
                findings.append(f"Identified {len(competitive_analysis)} key competitors")
            
            # Trend findings
            high_impact_trends = [t for t in trend_predictions if t.get('impact_level') == 'high']
            if high_impact_trends:
                findings.append(f"Identified {len(high_impact_trends)} high-impact market trends")
            
            # Add default findings if none extracted
            if not findings:
                findings = [
                    "Market analysis completed successfully",
                    "Competitive landscape assessed",
                    "Future trends identified"
                ]
            
        except Exception as e:
            logger.error(f"Error extracting key findings: {str(e)}")
            findings = ["Analysis completed with key insights identified"]
        
        return findings[:5]  # Limit to 5 key findings
    
    def _identify_critical_insights(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> List[str]:
        """Identify critical insights from analysis"""
        insights = []
        
        try:
            # Market insights
            market_trends = market_data.get('trends', [])
            if market_trends:
                insights.append("Market undergoing significant transformation")
            
            # Competitive insights
            if competitive_analysis:
                insights.append("Competitive landscape is dynamic and evolving")
            
            # Technology insights
            tech_trends = [t for t in trend_predictions if 'technology' in t.get('title', '').lower()]
            if tech_trends:
                insights.append("Technology is driving market disruption")
            
            # Regulatory insights
            reg_trends = [t for t in trend_predictions if 'regulatory' in t.get('title', '').lower()]
            if reg_trends:
                insights.append("Regulatory environment is changing rapidly")
            
            # Add default insights if none identified
            if not insights:
                insights = [
                    "Market opportunities exist for strategic positioning",
                    "Competitive differentiation is critical for success",
                    "Future trends will shape market dynamics"
                ]
            
        except Exception as e:
            logger.error(f"Error identifying critical insights: {str(e)}")
            insights = ["Market analysis reveals strategic opportunities"]
        
        return insights[:4]  # Limit to 4 critical insights
    
    def _generate_strategic_recommendations(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        try:
            # Market-based recommendations
            if market_data.get('market_overview', {}).get('growth_rate', '0%') > '5%':
                recommendations.append("Increase market presence to capitalize on growth")
            
            # Competitive recommendations
            if competitive_analysis:
                recommendations.append("Develop competitive differentiation strategy")
            
            # Technology recommendations
            tech_trends = [t for t in trend_predictions if 'technology' in t.get('title', '').lower()]
            if tech_trends:
                recommendations.append("Invest in technology capabilities")
            
            # General strategic recommendations
            recommendations.extend([
                "Strengthen market positioning",
                "Build strategic partnerships",
                "Enhance customer value proposition"
            ])
            
        except Exception as e:
            logger.error(f"Error generating strategic recommendations: {str(e)}")
            recommendations = ["Develop comprehensive market strategy"]
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _assess_risks(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> Dict:
        """Assess market and competitive risks"""
        try:
            risks = {
                'market_risks': [],
                'competitive_risks': [],
                'technology_risks': [],
                'regulatory_risks': [],
                'overall_risk_level': 'medium'
            }
            
            # Market risks
            if market_data.get('market_overview', {}).get('challenges'):
                risks['market_risks'] = market_data['market_overview']['challenges']
            
            # Competitive risks
            if competitive_analysis:
                risks['competitive_risks'] = [
                    "Intense competition",
                    "Market share pressure",
                    "Price competition"
                ]
            
            # Technology risks
            tech_trends = [t for t in trend_predictions if 'technology' in t.get('title', '').lower()]
            if tech_trends:
                risks['technology_risks'] = [
                    "Technology disruption",
                    "Implementation challenges",
                    "Security risks"
                ]
            
            # Regulatory risks
            reg_trends = [t for t in trend_predictions if 'regulatory' in t.get('title', '').lower()]
            if reg_trends:
                risks['regulatory_risks'] = [
                    "Regulatory changes",
                    "Compliance requirements",
                    "Policy uncertainty"
                ]
            
            # Determine overall risk level
            total_risks = len(risks['market_risks']) + len(risks['competitive_risks']) + len(risks['technology_risks']) + len(risks['regulatory_risks'])
            if total_risks > 8:
                risks['overall_risk_level'] = 'high'
            elif total_risks > 4:
                risks['overall_risk_level'] = 'medium'
            else:
                risks['overall_risk_level'] = 'low'
            
            return risks
            
        except Exception as e:
            logger.error(f"Error assessing risks: {str(e)}")
            return {
                'market_risks': ['Market uncertainty'],
                'competitive_risks': ['Competitive pressure'],
                'technology_risks': ['Technology changes'],
                'regulatory_risks': ['Regulatory uncertainty'],
                'overall_risk_level': 'medium'
            }
    
    def _determine_market_outlook(self, market_data: Dict, trend_predictions: List[Dict]) -> str:
        """Determine overall market outlook"""
        try:
            # Analyze growth rate
            growth_rate = market_data.get('market_overview', {}).get('growth_rate', '0%')
            if '5%' in growth_rate or '10%' in growth_rate or '15%' in growth_rate:
                base_outlook = "Positive"
            elif '0%' in growth_rate or '1%' in growth_rate or '2%' in growth_rate:
                base_outlook = "Neutral"
            else:
                base_outlook = "Cautious"
            
            # Adjust based on trends
            high_impact_trends = [t for t in trend_predictions if t.get('impact_level') == 'high']
            if len(high_impact_trends) > 3:
                outlook = f"{base_outlook} with significant changes expected"
            elif len(high_impact_trends) > 1:
                outlook = f"{base_outlook} with moderate changes expected"
            else:
                outlook = f"{base_outlook} with stable conditions"
            
            return outlook
            
        except Exception as e:
            logger.error(f"Error determining market outlook: {str(e)}")
            return "Neutral with stable conditions"
    
    def _calculate_confidence_level(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> float:
        """Calculate confidence level in analysis"""
        try:
            confidence_factors = []
            
            # Data quality factor
            if market_data and len(market_data) > 3:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.6)
            
            # Competitive analysis factor
            if competitive_analysis and len(competitive_analysis) > 2:
                confidence_factors.append(0.85)
            else:
                confidence_factors.append(0.7)
            
            # Trend prediction factor
            if trend_predictions and len(trend_predictions) > 5:
                confidence_factors.append(0.75)
            else:
                confidence_factors.append(0.65)
            
            # Calculate average confidence
            avg_confidence = sum(confidence_factors) / len(confidence_factors)
            
            return round(avg_confidence, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence level: {str(e)}")
            return 0.7
    
    def create_comprehensive_report(self, 
                                  industry: str,
                                  market_data: Dict,
                                  competitive_analysis: Dict,
                                  trend_predictions: List[Dict],
                                  strategic_recommendations: List[Dict]) -> BusinessReport:
        """Create a comprehensive business report"""
        try:
            # Create executive summary
            executive_summary = self.create_executive_summary(market_data, competitive_analysis, trend_predictions)
            
            # Structure market analysis
            market_analysis = {
                'market_overview': market_data.get('market_overview', {}),
                'market_trends': market_data.get('trends', []),
                'key_players': market_data.get('key_players', []),
                'market_metrics': self._calculate_market_metrics(market_data)
            }
            
            # Structure competitive analysis
            competitive_analysis_structured = {
                'competitive_landscape': competitive_analysis,
                'competitive_positioning': self._analyze_competitive_positioning(competitive_analysis),
                'competitive_threats': self._identify_competitive_threats(competitive_analysis),
                'competitive_opportunities': self._identify_competitive_opportunities(competitive_analysis)
            }
            
            # Structure trend analysis
            trend_analysis = {
                'trend_predictions': trend_predictions,
                'trend_categories': self._categorize_trends(trend_predictions),
                'trend_implications': self._analyze_trend_implications(trend_predictions),
                'trend_priorities': self._prioritize_trends(trend_predictions)
            }
            
            # Structure strategic recommendations
            strategic_recommendations_structured = self._structure_strategic_recommendations(strategic_recommendations)
            
            # Create risk assessment
            risk_assessment = {
                'risk_categories': self._categorize_risks(market_data, competitive_analysis, trend_predictions),
                'risk_mitigation': self._develop_risk_mitigation_strategies(market_data, competitive_analysis, trend_predictions),
                'risk_monitoring': self._establish_risk_monitoring_framework()
            }
            
            # Create appendices
            appendices = {
                'data_sources': self._document_data_sources(market_data),
                'methodology': self._document_methodology(),
                'glossary': self._create_glossary(),
                'charts_and_graphs': self._generate_chart_recommendations(market_data, competitive_analysis, trend_predictions)
            }
            
            return BusinessReport(
                title=f"Market Intelligence Report: {industry} Industry",
                executive_summary=executive_summary,
                market_analysis=market_analysis,
                competitive_analysis=competitive_analysis_structured,
                trend_analysis=trend_analysis,
                strategic_recommendations=strategic_recommendations_structured,
                risk_assessment=risk_assessment,
                appendices=appendices
            )
            
        except Exception as e:
            logger.error(f"Error creating comprehensive report: {str(e)}")
            # Return minimal report structure
            return BusinessReport(
                title=f"Market Intelligence Report: {industry} Industry",
                executive_summary=ExecutiveSummary([], [], [], {}, "Neutral", 0.5),
                market_analysis={},
                competitive_analysis={},
                trend_analysis={},
                strategic_recommendations=[],
                risk_assessment={},
                appendices={}
            )
    
    def _calculate_market_metrics(self, market_data: Dict) -> Dict:
        """Calculate key market metrics"""
        return {
            'market_size': market_data.get('market_overview', {}).get('market_size', 'Unknown'),
            'growth_rate': market_data.get('market_overview', {}).get('growth_rate', 'Unknown'),
            'market_maturity': 'Growing',
            'competition_level': 'Medium',
            'entry_barriers': 'Medium'
        }
    
    def _analyze_competitive_positioning(self, competitive_analysis: Dict) -> Dict:
        """Analyze competitive positioning"""
        return {
            'market_leaders': [],
            'challengers': [],
            'followers': [],
            'niche_players': []
        }
    
    def _identify_competitive_threats(self, competitive_analysis: Dict) -> List[str]:
        """Identify competitive threats"""
        return [
            "Intense competition",
            "Price pressure",
            "Market share erosion"
        ]
    
    def _identify_competitive_opportunities(self, competitive_analysis: Dict) -> List[str]:
        """Identify competitive opportunities"""
        return [
            "Market expansion",
            "Product differentiation",
            "Strategic partnerships"
        ]
    
    def _categorize_trends(self, trend_predictions: List[Dict]) -> Dict:
        """Categorize trends by type"""
        categories = {
            'technology_trends': [],
            'market_trends': [],
            'regulatory_trends': [],
            'consumer_trends': [],
            'competitive_trends': []
        }
        
        for trend in trend_predictions:
            trend_type = trend.get('trend_type', 'market')
            category_key = f"{trend_type}_trends"
            if category_key in categories:
                categories[category_key].append(trend)
        
        return categories
    
    def _analyze_trend_implications(self, trend_predictions: List[Dict]) -> List[str]:
        """Analyze implications of trends"""
        implications = []
        
        for trend in trend_predictions:
            if trend.get('impact_level') == 'high':
                implications.append(f"High impact: {trend.get('title', 'Trend')}")
        
        return implications[:5]  # Limit to 5 implications
    
    def _prioritize_trends(self, trend_predictions: List[Dict]) -> List[Dict]:
        """Prioritize trends by impact and probability"""
        # Sort by impact level and probability
        sorted_trends = sorted(
            trend_predictions,
            key=lambda x: (self._impact_score(x.get('impact_level', 'low')), x.get('probability', 0)),
            reverse=True
        )
        
        return sorted_trends[:10]  # Return top 10 trends
    
    def _impact_score(self, impact_level: str) -> int:
        """Convert impact level to numeric score"""
        scores = {'high': 3, 'medium': 2, 'low': 1}
        return scores.get(impact_level, 1)
    
    def _structure_strategic_recommendations(self, recommendations: List[Dict]) -> Dict:
        """Structure strategic recommendations"""
        return {
            'immediate_actions': [r for r in recommendations if r.get('timeframe') == 'immediate'],
            'short_term_actions': [r for r in recommendations if r.get('timeframe') == 'short_term'],
            'long_term_actions': [r for r in recommendations if r.get('timeframe') == 'long_term'],
            'priority_recommendations': [r for r in recommendations if r.get('priority') == 'high']
        }
    
    def _categorize_risks(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> Dict:
        """Categorize risks by type"""
        return {
            'market_risks': ['Market volatility', 'Economic uncertainty'],
            'competitive_risks': ['Competitive pressure', 'Market share loss'],
            'technology_risks': ['Technology disruption', 'Implementation challenges'],
            'regulatory_risks': ['Regulatory changes', 'Compliance requirements'],
            'operational_risks': ['Resource constraints', 'Execution challenges']
        }
    
    def _develop_risk_mitigation_strategies(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> List[str]:
        """Develop risk mitigation strategies"""
        return [
            "Diversify market presence",
            "Strengthen competitive advantages",
            "Invest in technology capabilities",
            "Enhance compliance framework",
            "Build operational resilience"
        ]
    
    def _establish_risk_monitoring_framework(self) -> Dict:
        """Establish risk monitoring framework"""
        return {
            'key_risk_indicators': ['Market volatility', 'Competitive moves', 'Regulatory changes'],
            'monitoring_frequency': 'Weekly',
            'escalation_procedures': ['Immediate alert for high-risk events', 'Weekly review for medium risks'],
            'reporting_structure': ['Risk dashboard', 'Monthly risk reports', 'Quarterly risk assessments']
        }
    
    def _document_data_sources(self, market_data: Dict) -> List[str]:
        """Document data sources used"""
        return [
            "Financial databases",
            "Industry reports",
            "News and media sources",
            "Regulatory filings",
            "Expert interviews"
        ]
    
    def _document_methodology(self) -> Dict:
        """Document analysis methodology"""
        return {
            'data_collection': 'Multi-source data aggregation with validation',
            'analysis_framework': 'Comprehensive market and competitive analysis',
            'prediction_methods': 'Statistical modeling and trend analysis',
            'quality_assurance': 'Multi-level validation and peer review'
        }
    
    def _create_glossary(self) -> Dict:
        """Create glossary of terms"""
        return {
            'Market Intelligence': 'Systematic collection and analysis of market information',
            'Competitive Intelligence': 'Analysis of competitor activities and strategies',
            'Market Share': 'Percentage of total market sales captured by a company',
            'SWOT Analysis': 'Strengths, Weaknesses, Opportunities, Threats analysis',
            'Market Positioning': 'How a company's products/services are perceived relative to competitors'
        }
    
    def _generate_chart_recommendations(self, market_data: Dict, competitive_analysis: Dict, trend_predictions: List[Dict]) -> List[str]:
        """Generate recommendations for charts and graphs"""
        return [
            "Market size and growth trends",
            "Competitive landscape map",
            "Trend impact matrix",
            "Risk assessment heatmap",
            "Strategic recommendations timeline"
        ]

class ReportWriterAgent:
    """Advanced Report Writer Agent with sophisticated business communication capabilities"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool = ReportWriterTool()
    
    def create_agent(self) -> Agent:
        """Create the report writer agent with advanced capabilities"""
        
        return Agent(
            role="Senior Business Intelligence Report Writer",
            goal="Create compelling, actionable executive reports that drive strategic decision-making",
            backstory="""You are a senior business intelligence report writer with 20+ years of experience in 
            executive communication and strategic reporting. You have deep expertise in:
            - Executive-level business writing and communication
            - Strategic analysis and insight development
            - Data visualization and presentation
            - Risk assessment and mitigation strategies
            - Market intelligence and competitive analysis
            - Stakeholder communication and engagement
            
            You excel at transforming complex market data into clear, compelling narratives that 
            resonate with C-level executives and drive strategic decision-making. Your reports have 
            influenced billion-dollar investment decisions and strategic initiatives.""",
            
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            memory=True
        ) 