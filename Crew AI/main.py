#!/usr/bin/env python3
"""
AI-Powered Business Intelligence & Market Research Platform
Main application entry point with advanced Crew AI orchestration
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from crewai import Crew, Agent, Task, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from agents.data_collector import DataCollectorAgent
from agents.market_analyzer import MarketAnalyzerAgent
from agents.competitor_monitor import CompetitorMonitorAgent
from agents.trend_predictor import TrendPredictorAgent
from agents.report_writer import ReportWriterAgent
from services.data_service import DataService
from services.market_service import MarketService
from config.settings import Settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BusinessIntelligenceCrew:
    """
    Advanced Crew AI orchestration for business intelligence and market research
    Demonstrates master-level skills in multi-agent coordination and complex workflows
    """
    
    def __init__(self):
        self.settings = Settings()
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            api_key=self.settings.openai_api_key
        )
        
        # Initialize services
        self.data_service = DataService()
        self.market_service = MarketService()
        
        # Initialize agents with advanced capabilities
        self.agents = self._initialize_agents()
        
        # Create the main crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=[],
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize specialized agents with advanced capabilities"""
        
        agents = {
            'data_collector': DataCollectorAgent(
                llm=self.llm,
                data_service=self.data_service
            ).create_agent(),
            
            'market_analyzer': MarketAnalyzerAgent(
                llm=self.llm,
                market_service=self.market_service
            ).create_agent(),
            
            'competitor_monitor': CompetitorMonitorAgent(
                llm=self.llm,
                data_service=self.data_service
            ).create_agent(),
            
            'trend_predictor': TrendPredictorAgent(
                llm=self.llm,
                market_service=self.market_service
            ).create_agent(),
            
            'report_writer': ReportWriterAgent(
                llm=self.llm
            ).create_agent()
        }
        
        return agents
    
    async def run_market_analysis(self, 
                                industry: str, 
                                companies: List[str] = None,
                                analysis_depth: str = "comprehensive") -> Dict:
        """
        Execute comprehensive market analysis workflow
        Demonstrates advanced Crew AI orchestration with conditional logic
        """
        
        logger.info(f"Starting market analysis for industry: {industry}")
        
        # Create dynamic tasks based on analysis requirements
        tasks = []
        
        # Task 1: Data Collection
        data_collection_task = Task(
            description=f"""
            Collect comprehensive market data for the {industry} industry.
            
            Requirements:
            - Gather financial data from multiple sources (Yahoo Finance, Alpha Vantage, etc.)
            - Collect news and social media sentiment data
            - Gather competitive intelligence data
            - Collect market trends and industry reports
            - Focus on companies: {companies if companies else 'all major players'}
            
            Analysis Depth: {analysis_depth}
            
            Output: Structured dataset with timestamps, sources, and confidence scores
            """,
            agent=self.agents['data_collector'],
            expected_output="Comprehensive dataset with market data, news, and competitive intelligence"
        )
        tasks.append(data_collection_task)
        
        # Task 2: Market Analysis (conditional based on data availability)
        market_analysis_task = Task(
            description=f"""
            Analyze the collected market data for {industry} industry.
            
            Analysis Requirements:
            - Perform SWOT analysis for key players
            - Identify market trends and patterns
            - Analyze competitive landscape
            - Assess market opportunities and threats
            - Calculate key performance indicators
            
            Use advanced analytical techniques including:
            - Statistical analysis
            - Sentiment analysis
            - Trend detection algorithms
            - Competitive positioning analysis
            
            Output: Detailed market analysis report with insights and recommendations
            """,
            agent=self.agents['market_analyzer'],
            expected_output="Comprehensive market analysis with insights, trends, and recommendations",
            context=[data_collection_task]
        )
        tasks.append(market_analysis_task)
        
        # Task 3: Competitor Monitoring (if companies specified)
        if companies:
            competitor_task = Task(
                description=f"""
                Monitor and analyze competitors: {', '.join(companies)}
                
                Analysis Requirements:
                - Track competitor performance metrics
                - Monitor product launches and strategic moves
                - Analyze pricing strategies
                - Assess market positioning
                - Identify competitive advantages and weaknesses
                
                Output: Competitive intelligence report with actionable insights
                """,
                agent=self.agents['competitor_monitor'],
                expected_output="Competitive intelligence report with detailed competitor analysis",
                context=[data_collection_task]
            )
            tasks.append(competitor_task)
        
        # Task 4: Trend Prediction
        trend_prediction_task = Task(
            description=f"""
            Predict future market trends for {industry} industry.
            
            Prediction Requirements:
            - Use historical data and current trends
            - Apply machine learning models for forecasting
            - Predict market growth and opportunities
            - Identify potential risks and challenges
            - Forecast competitive landscape changes
            
            Use advanced prediction techniques:
            - Time series analysis
            - Machine learning algorithms
            - Sentiment-based forecasting
            - Market simulation models
            
            Output: Predictive analysis with confidence intervals and scenarios
            """,
            agent=self.agents['trend_predictor'],
            expected_output="Predictive analysis with future trends, scenarios, and confidence levels",
            context=[market_analysis_task]
        )
        tasks.append(trend_prediction_task)
        
        # Task 5: Executive Report Generation
        report_task = Task(
            description=f"""
            Create an executive-level market intelligence report for {industry}.
            
            Report Requirements:
            - Executive summary with key insights
            - Market overview and current state
            - Competitive analysis and positioning
            - Future trends and predictions
            - Strategic recommendations
            - Risk assessment and mitigation strategies
            
            Format: Professional business report with:
            - Executive summary
            - Detailed analysis sections
            - Visual charts and graphs
            - Actionable recommendations
            - Risk assessment matrix
            
            Target Audience: C-level executives and strategic decision makers
            """,
            agent=self.agents['report_writer'],
            expected_output="Professional executive report with insights, recommendations, and visualizations",
            context=[market_analysis_task, trend_prediction_task]
        )
        tasks.append(report_task)
        
        # Update crew with tasks
        self.crew.tasks = tasks
        
        try:
            # Execute the crew workflow
            result = await self.crew.kickoff()
            
            # Process and structure the results
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'industry': industry,
                'analysis_depth': analysis_depth,
                'companies_analyzed': companies,
                'executive_summary': result.get('executive_summary', ''),
                'market_insights': result.get('market_insights', []),
                'competitive_analysis': result.get('competitive_analysis', {}),
                'trend_predictions': result.get('trend_predictions', []),
                'strategic_recommendations': result.get('recommendations', []),
                'risk_assessment': result.get('risk_assessment', {}),
                'data_sources': result.get('data_sources', []),
                'confidence_score': result.get('confidence_score', 0.0),
                'processing_time': result.get('processing_time', 0)
            }
            
            logger.info(f"Market analysis completed successfully for {industry}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            raise
    
    async def run_continuous_monitoring(self, 
                                      industry: str, 
                                      monitoring_interval: int = 3600) -> None:
        """
        Continuous market monitoring with real-time updates
        Demonstrates advanced Crew AI with scheduling and real-time processing
        """
        
        logger.info(f"Starting continuous monitoring for {industry}")
        
        while True:
            try:
                # Run quick market analysis
                result = await self.run_market_analysis(
                    industry=industry,
                    analysis_depth="monitoring"
                )
                
                # Store results for real-time dashboard
                await self.data_service.store_monitoring_result(result)
                
                # Send alerts for significant changes
                await self._check_for_alerts(result)
                
                logger.info(f"Monitoring cycle completed for {industry}")
                
                # Wait for next cycle
                await asyncio.sleep(monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _check_for_alerts(self, analysis_result: Dict) -> None:
        """Check for significant market changes and send alerts"""
        # Implementation for alert system
        pass

# FastAPI application
app = FastAPI(
    title="AI-Powered Business Intelligence Platform",
    description="Advanced Crew AI platform for market research and business intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global crew instance
business_intelligence_crew = None

@app.on_event("startup")
async def startup_event():
    """Initialize the business intelligence crew on startup"""
    global business_intelligence_crew
    business_intelligence_crew = BusinessIntelligenceCrew()
    logger.info("Business Intelligence Crew initialized successfully")

@app.post("/api/analyze-market")
async def analyze_market(
    industry: str,
    companies: List[str] = None,
    analysis_depth: str = "comprehensive",
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint for market analysis requests
    Demonstrates API integration with Crew AI workflows
    """
    
    if not business_intelligence_crew:
        return {"error": "Crew not initialized"}
    
    try:
        result = await business_intelligence_crew.run_market_analysis(
            industry=industry,
            companies=companies,
            analysis_depth=analysis_depth
        )
        
        return {
            "status": "success",
            "data": result,
            "message": f"Market analysis completed for {industry}"
        }
        
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/start-monitoring")
async def start_monitoring(
    industry: str,
    monitoring_interval: int = 3600
):
    """Start continuous market monitoring"""
    
    if not business_intelligence_crew:
        return {"error": "Crew not initialized"}
    
    # Start monitoring in background
    asyncio.create_task(
        business_intelligence_crew.run_continuous_monitoring(
            industry=industry,
            monitoring_interval=monitoring_interval
        )
    )
    
    return {
        "status": "success",
        "message": f"Continuous monitoring started for {industry}"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "crew_initialized": business_intelligence_crew is not None
    }

if __name__ == "__main__":
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 