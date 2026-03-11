import os
import json
import httpx
import logging
from typing import List, Dict, Optional
from datetime import datetime
from langchain.agents import Tool
from langchain.agents import AgentExecutor
from langchain.agents import initialize_agent
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import BaseTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepResearchAgent:
    def __init__(self):
        # Get API keys from environment variables
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.perplexity_api_key:
            logger.error("PERPLEXITY_API_KEY not found in environment variables")
            raise ValueError("PERPLEXITY_API_KEY environment variable is required")

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self._create_agent()

    def _create_agent(self):
        try:
            # Initialize tools
            tools = self._get_research_tools()
            
            # Initialize the agent with ChatOpenAI
            self.agent = initialize_agent(
                tools=tools,
                llm=ChatOpenAI(
                    temperature=0,
                    model_name="gpt-4",
                    api_key=self.openai_api_key
                ),
                agent="zero-shot-react-description",
                verbose=True
            )
            logger.info("Research agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise

    def _get_research_tools(self) -> List[Tool]:
        return [
            Tool(
                name="deep_research",
                func=self.perform_deep_research,
                description="Perform deep research on a given topic using Perplexity API"
            )
        ]

    async def perform_deep_research(self, query: str) -> Dict:
        """Perform deep research using Perplexity API"""
        headers = {
            "Authorization": f"Bearer {self.perplexity_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a financial analyst specializing in Nepal Stock Exchange (NEPSE). Provide detailed, accurate analysis with specific numbers and facts."
                },
                {"role": "user", "content": query}
            ],
            "max_tokens": 8000,
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.perplexity_url, 
                    headers=headers, 
                    json=payload, 
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                logger.info("Successfully received response from Perplexity API")
                return result
            except httpx.HTTPError as e:
                logger.error(f"HTTP error during Perplexity API call: {str(e)}")
                if hasattr(e, 'response'):
                    logger.error(f"Error details: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during API call: {str(e)}")
                raise

    async def get_stock_news(self, stock_symbol: str = None) -> List[Dict]:
        """Get comprehensive news and analysis for a stock"""
        try:
            if stock_symbol:
                query = (
                    f"Analyze the latest news, market sentiment, and key developments for {stock_symbol} "
                    f"stock in NEPSE market. Include:\n"
                    f"1. Recent price movements and trading volume\n"
                    f"2. Technical analysis indicators\n"
                    f"3. Fundamental analysis metrics\n"
                    f"4. Recent corporate announcements\n"
                    f"5. Sector-specific trends affecting {stock_symbol}"
                )
            else:
                query = (
                    "Analyze the overall NEPSE market conditions, including:\n"
                    "1. Major market movers\n"
                    "2. Sector-wise performance\n"
                    "3. Market breadth and sentiment\n"
                    "4. Key technical levels\n"
                    "5. Important market events and news"
                )

            research_result = await self.perform_deep_research(query)
            
            content = research_result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                logger.warning("No content received from research")
                return []

            return [{
                "source": "Perplexity Deep Research",
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.9
            }]
        except Exception as e:
            logger.error(f"Error in get_stock_news: {str(e)}")
            return []

    async def run(self, query: str = None) -> Dict:
        """Run deep research analysis"""
        try:
            if not query:
                query = (
                    "Provide a comprehensive analysis of the current NEPSE market, including:\n"
                    "1. Overall market trend and sentiment\n"
                    "2. Key market indicators and their implications\n"
                    "3. Sector-wise performance analysis\n"
                    "4. Major market moving events\n"
                    "5. Technical analysis of market indices"
                )

            research_result = await self.perform_deep_research(query)
            
            content = research_result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if not content:
                raise ValueError("No content received from research")

            return {
                "analysis": content,
                "timestamp": datetime.utcnow().isoformat(),
                "model": "sonar-deep-research",
                "confidence": 0.9
            }
        except Exception as e:
            logger.error(f"Error in run method: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }