import asyncio
import json
import time
import httpx
import redis.asyncio as redis
import asyncpg
from fastapi import FastAPI, WebSocket, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Optional, Dict
import backoff
import socket
import logging
from datetime import datetime
from nepse_news_agent import DeepResearchAgent
from nepse_trading_agent import NepseTradingAgent, TradingAgentError, DataFetchError, AnalysisError

# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -------------------------
# Global Variables
# -------------------------
app = FastAPI()
r: Optional[redis.Redis] = None
pg_conn: Optional[asyncpg.Connection] = None
research_agent: Optional[DeepResearchAgent] = None
trading_agent: Optional[NepseTradingAgent] = None
# Global variable for fetching loop task
fetch_loop_task: Optional[asyncio.Task] = None

# -------------------------
# CORS Middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Connection Helpers
# -------------------------
@backoff.on_exception(backoff.expo, Exception, max_tries=5, on_backoff=lambda e: logger.warning(f"Retrying Redis connection: {e}"))
async def connect_to_redis():
    """Connect to Redis"""
    try:
        redis_url = "redis://redis:6379"
        client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        logger.info("Successfully connected to Redis")
        return client
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        raise

@backoff.on_exception(backoff.expo, Exception, max_tries=5, on_backoff=lambda e: logger.warning(f"Retrying PostgreSQL connection: {e}"))
async def connect_to_db():
    """Connect to PostgreSQL"""
    try:
        conn = await asyncpg.connect(
            user='karol',
            password='Karol@123',
            database='nepse',
            host='timescale'
        )
        logger.info("Successfully connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise

async def wait_for_service(host, port, service_name):
    """Wait for a service to be available"""
    while True:
        try:
            with socket.create_connection((host, port), timeout=1) as sock:
                logger.info(f"{service_name} is available at {host}:{port}")
                break
        except (ConnectionRefusedError, socket.timeout):
            logger.warning(f"Waiting for {service_name} at {host}:{port}...")
            await asyncio.sleep(1)

async def wait_for_services():
    """Wait for all required services to be available"""
    await asyncio.gather(
        wait_for_service("redis", 6379, "Redis"),
        wait_for_service("timescale", 5432, "TimescaleDB")
    )

# -------------------------
# Agent Initialization
# -------------------------
async def initialize_research_agent():
    """Initialize the deep research agent"""
    global research_agent
    try:
        research_agent = DeepResearchAgent()
        logger.info("DeepResearchAgent initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing DeepResearchAgent: {e}", exc_info=True)

async def initialize_trading_agent():
    """Initialize the trading signal agent"""
    global trading_agent
    try:
        if not pg_conn or not r:
            logger.error("Database connections not ready for trading agent")
            return
        # Test PostgreSQL connection
        logger.info("Testing PostgreSQL connection...")
        await pg_conn.execute("SELECT 1")
        logger.info("PostgreSQL connection is working.")

        # Test Redis connection
        logger.info("Testing Redis connection...")
        await r.ping()
        logger.info("Redis connection is working.")

        trading_agent = NepseTradingAgent(pg_conn, r)
        logger.info("NepseTradingAgent initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing NepseTradingAgent: {e}", exc_info=True)

# -------------------------
# Event Handlers
# -------------------------
async def _create_tables():
    """Create necessary database tables if they don't exist"""
    try:
        # Create stock_data table
        await pg_conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_data (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                company_name VARCHAR(255),
                current_price DECIMAL(10,2),
                percentage_change DECIMAL(10,2),
                volume DECIMAL(20,2),
                previous_closing DECIMAL(10,2),
                open_price DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                fifty_two_week_high DECIMAL(10,2),
                fifty_two_week_low DECIMAL(10,2),
                market_capitalization DECIMAL(20,2),
                pe_ratio DECIMAL(10,2),
                eps DECIMAL(10,2),
                book_value DECIMAL(10,2),
                dividend_yield DECIMAL(10,2),
                last_traded_on VARCHAR(50),
                week_change DECIMAL(10,2),
                day_change DECIMAL(10,2),
                timestamp DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timestamp)
            );
            
            -- Create index on symbol and timestamp for faster queries
            CREATE INDEX IF NOT EXISTS idx_stock_data_symbol_timestamp 
            ON stock_data(symbol, timestamp);
            
            -- Create index on timestamp for time-based queries
            CREATE INDEX IF NOT EXISTS idx_stock_data_timestamp 
            ON stock_data(timestamp);
        """)
        
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize connections and start data fetching on startup"""
    global r, pg_conn, research_agent, trading_agent, fetch_loop_task
    
    try:
        # Wait for services to be ready
        await wait_for_services()
        
        # Connect to Redis
        r = await connect_to_redis()
        
        # Connect to PostgreSQL
        pg_conn = await connect_to_db()
        
        # Create database tables
        await _create_tables()
        
        # Initialize agents
        await initialize_research_agent()
        await initialize_trading_agent()
        
        # Start data fetching loop
        fetch_loop_task = asyncio.create_task(fetch_loop())
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event: close connections and stop tasks"""
    global r, pg_conn, fetch_loop_task

    logger.info("Shutting down application...")

    if fetch_loop_task:
        fetch_loop_task.cancel()
        try:
            await fetch_loop_task
        except asyncio.CancelledError:
            logger.info("Data fetch loop cancelled successfully")

    if r:
        await r.close()
        logger.info("Redis connection closed")
    if pg_conn:
        await pg_conn.close()
        logger.info("PostgreSQL connection closed")

# -------------------------
# Data Fetching Logic
# -------------------------
@backoff.on_exception(backoff.expo, httpx.RequestError, max_tries=3, on_backoff=lambda e: logger.warning(f"Retrying data fetch: {e}"))
async def fetch_merolagani_data():
    """Fetch live data from Merolagani"""
    url = "https://merolagani.com/handlers/webrequesthandler.ashx"
    params = {
        "type": "market_summary"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://merolagani.com/",
        "Origin": "https://merolagani.com"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Debugging: Print raw response content
            raw_content = response.text
            logger.debug(f"Raw Merolagani response: {raw_content[:500]}") # Print first 500 chars

            if not raw_content.strip():
                logger.warning("Received empty response from Merolagani API. Skipping JSON decoding.")
                return None

            try:
                data = response.json()
                if not data or not isinstance(data, dict):
                    logger.error(f"Invalid data format received from Merolagani API: {raw_content[:500]}")
                    return None
                    
                # The site changed structure. Prefer COMPANY_DATA if present; otherwise use turnover.detail list.
                if 'COMPANY_DATA' in data:
                    logger.debug("Successfully fetched COMPANY_DATA from Merolagani")
                    return {'COMPANY_DATA': data['COMPANY_DATA']}

                # Fallback: build COMPANY_DATA from turnover.detail structure
                if isinstance(data.get('turnover', {}).get('detail'), list):
                    company_list = []
                    for item in data['turnover']['detail']:
                        company_list.append({
                            'symbol': item.get('s'),
                            'companyName': item.get('n', ''),
                            'currentPrice': item.get('lp'),
                            'percentageChange': item.get('pc'),
                            'high': item.get('h'),
                            'low': item.get('l'),
                            'open': item.get('op'),
                            'volume': item.get('q'),
                        })
                    logger.debug(f"Converted {len(company_list)} items from turnover.detail")
                    return {'COMPANY_DATA': company_list}

                logger.error("Unrecognized data format in Merolagani API response")
                return None
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed during data fetch. Raw content: {raw_content}")
                raise e

    except httpx.RequestError as e:
        logger.error(f"HTTP request failed during data fetch: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during data fetch: {e}")
        raise

async def process_and_store_data(data):
    """Process and store fetched data into PostgreSQL and Redis"""
    if not pg_conn:
        logger.error("PostgreSQL connection not available for data storage.")
        return

    try:
        async with pg_conn.transaction():
            # Store in PostgreSQL
            insert_query = """
            INSERT INTO stock_data (
                symbol, company_name, current_price, percentage_change, volume,
                previous_closing, open_price, high_price, low_price,
                fifty_two_week_high, fifty_two_week_low,
                market_capitalization, pe_ratio, eps, book_value,
                dividend_yield, last_traded_on, week_change, day_change,
                timestamp
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            ON CONFLICT (symbol, timestamp) DO UPDATE SET
                current_price = EXCLUDED.current_price,
                percentage_change = EXCLUDED.percentage_change,
                volume = EXCLUDED.volume,
                previous_closing = EXCLUDED.previous_closing,
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                fifty_two_week_high = EXCLUDED.fifty_two_week_high,
                fifty_two_week_low = EXCLUDED.fifty_two_week_low,
                market_capitalization = EXCLUDED.market_capitalization,
                pe_ratio = EXCLUDED.pe_ratio,
                eps = EXCLUDED.eps,
                book_value = EXCLUDED.book_value,
                dividend_yield = EXCLUDED.dividend_yield,
                last_traded_on = EXCLUDED.last_traded_on,
                week_change = EXCLUDED.week_change,
                day_change = EXCLUDED.day_change,
                updated_at = NOW();
            """
            
            current_timestamp = datetime.now().timestamp()
            
            for stock in data.get('COMPANY_DATA', []):
                try:
                    symbol = stock.get('symbol')
                    if not symbol:
                        logger.warning("Skipping stock with missing symbol")
                        continue

                    # Always provide all required columns, even if missing in API
                    current_price = float(stock.get('currentPrice', 0) or stock.get('current_price', 0) or 0)
                    percentage_change = float(stock.get('percentageChange', 0) or stock.get('percentage_change', 0) or 0)
                    volume = float(stock.get('volume', 0) or 0)
                    previous_closing = float(stock.get('previousClosing', 0) or stock.get('previous_closing', 0) or 0)
                    open_price = float(stock.get('open', 0) or stock.get('open_price', 0) or 0)
                    high_price = float(stock.get('high', 0) or stock.get('high_price', 0) or 0)
                    low_price = float(stock.get('low', 0) or stock.get('low_price', 0) or 0)
                    fifty_two_week_high = float(stock.get('fiftyTwoWeekHigh', 0) or stock.get('fifty_two_week_high', 0) or 0)
                    fifty_two_week_low = float(stock.get('fiftyTwoWeekLow', 0) or stock.get('fifty_two_week_low', 0) or 0)
                    market_capitalization = float(stock.get('marketCapitalization', 0) or stock.get('market_capitalization', 0) or 0)
                    pe_ratio = float(stock.get('peRatio', 0) or stock.get('pe_ratio', 0) or 0)
                    eps = float(stock.get('eps', 0) or 0)
                    book_value = float(stock.get('bookValue', 0) or stock.get('book_value', 0) or 0)
                    dividend_yield = float(stock.get('dividendYield', 0) or stock.get('dividend_yield', 0) or 0)
                    week_change = float(stock.get('weekChange', 0) or stock.get('week_change', 0) or 0)
                    day_change = float(stock.get('dayChange', 0) or stock.get('day_change', 0) or 0)
                    
                    await pg_conn.execute(
                        insert_query,
                        symbol,
                        stock.get('companyName', ''),
                        current_price,
                        percentage_change,
                        volume,
                        previous_closing,
                        open_price,
                        high_price,
                        low_price,
                        fifty_two_week_high,
                        fifty_two_week_low,
                        market_capitalization,
                        pe_ratio,
                        eps,
                        book_value,
                        dividend_yield,
                        stock.get('lastTradedOn', ''),
                        week_change,
                        day_change,
                        current_timestamp
                    )
                except (ValueError, TypeError) as e:
                    logger.error(f"Error processing stock data for {symbol}: {e}")
                    continue
                    
            logger.info(f"Stored {len(data.get('COMPANY_DATA', []))} stock data points to PostgreSQL")

            # Store in Redis
            if r:
                try:
                    data['timestamp'] = current_timestamp
                    await r.set("latest_market_data", json.dumps(data))
                    logger.info("Stored latest market data to Redis")
                except Exception as e:
                    logger.error(f"Error storing data to Redis: {e}")
            else:
                logger.warning("Redis connection not available, skipping Redis storage.")

    except Exception as e:
        logger.error(f"Error processing or storing data: {e}", exc_info=True)

async def fetch_loop():
    """Periodically fetches and stores market data"""
    while True:
        try:
            data = await fetch_merolagani_data()
            if data:
                await process_and_store_data(data)
            await asyncio.sleep(5)  # Fetch every 5 seconds
        except asyncio.CancelledError:
            logger.info("Fetch loop cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in fetch loop: {e}", exc_info=True)
            await asyncio.sleep(5) # Wait before retrying to prevent rapid error looping

# -------------------------
# API Endpoints
# -------------------------
@app.get("/")
async def read_root():
    """Root endpoint for API information"""
    return {"message": "Welcome to Nepse AI Agent API", "status": "running"}

@app.get("/latest")
async def get_latest_market_data() -> Dict:
    logger.info("Received request for latest market data")
    if not r:
        logger.error("Redis connection not available for /latest endpoint")
        raise HTTPException(status_code=503, detail="Redis connection not available")
    try:
        data = await r.get("latest_market_data")
        if data:
            return json.loads(data)
        raise HTTPException(status_code=404, detail="Latest market data not found")
    except Exception as e:
        logger.error(f"Error fetching latest market data from Redis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching latest data")

@app.get("/history")
async def get_historical_data(
    from_ts: Optional[int] = Query(None, description="Start Unix timestamp"),
    to_ts: Optional[int] = Query(None, description="End Unix timestamp"),
    stock_symbol: Optional[str] = Query(None, description="Optional stock symbol to filter by")
) -> List[Dict]:
    logger.info(f"Received request for historical data: from_ts={from_ts}, to_ts={to_ts}, stock_symbol={stock_symbol}")
    if not pg_conn:
        logger.error("PostgreSQL connection not available for /history endpoint")
        raise HTTPException(status_code=503, detail="Database connection not available")

    query = "SELECT * FROM stock_data WHERE TRUE"
    params = []
    param_count = 1

    if from_ts:
        query += f" AND created_at >= to_timestamp(${param_count})"
        params.append(from_ts)
        param_count += 1
    if to_ts:
        query += f" AND created_at <= to_timestamp(${param_count})"
        params.append(to_ts)
        param_count += 1
    if stock_symbol:
        query += f" AND symbol = ${param_count}"
        params.append(stock_symbol.upper())
        param_count += 1

    query += " ORDER BY created_at DESC"

    try:
        records = await pg_conn.fetch(query, *params)
        return [dict(r) for r in records]
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching historical data")

@app.get("/stocks")
async def get_all_stock_symbols() -> List[str]:
    logger.info("Received request for all stock symbols")
    if not pg_conn:
        logger.error("PostgreSQL connection not available for /stocks endpoint")
        raise HTTPException(status_code=503, detail="Database connection not available")
    try:
        records = await pg_conn.fetch("SELECT DISTINCT symbol FROM stock_data ORDER BY symbol")
        return [r["symbol"] for r in records]
    except Exception as e:
        logger.error(f"Error fetching stock symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching stock symbols")

@app.get("/research")
async def get_market_research(background_tasks: BackgroundTasks) -> Dict:
    logger.info("Received request for market research")
    if not research_agent:
        logger.error("DeepResearchAgent not initialized for /research endpoint")
        raise HTTPException(status_code=503, detail="Research agent not available")
    try:
        # Get latest data from Redis for research context
        latest_data_raw = await r.get("latest_market_data") if r else None
        latest_data = json.loads(latest_data_raw) if latest_data_raw else {}

        # The research agent runs a complex task, so we run it in a background task
        # and immediately return a status. The client can poll for results if needed.
        # For simplicity, this example directly awaits the result.
        # In a real-world scenario, you might use a task queue (e.g., Celery)
        # or store results in Redis for later retrieval.
        market_summary = latest_data.get('MARKET_SUMMARY', {})
        top_gainers = latest_data.get('TOP_GAINERS', [])
        top_losers = latest_data.get('TOP_LOSERS', [])

        prompt_data = {
            "market_summary": market_summary,
            "top_gainers": top_gainers,
            "top_losers": top_losers
        }
        
        # This will block the API call until research is complete.
        # For long-running tasks, consider a background task and status polling.
        # For this example, we directly await it as per previous code structure.
        research_result = await research_agent.run_deep_research(json.dumps(prompt_data))
        return {"status": "success", "research_report": research_result}
    except Exception as e:
        logger.error(f"Error running market research: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/research/stock/{symbol}")
async def get_stock_research(symbol: str, background_tasks: BackgroundTasks) -> Dict:
    logger.info(f"Received request for stock research: symbol={symbol}")
    if not research_agent:
        logger.error("DeepResearchAgent not initialized for /research/stock/{symbol} endpoint")
        raise HTTPException(status_code=503, detail="Research agent not available")
    if not pg_conn:
        logger.error("PostgreSQL connection not available for stock research")
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        # Fetch latest data for the specific stock
        stock_data = await pg_conn.fetchrow("SELECT * FROM stock_data WHERE symbol = $1 ORDER BY created_at DESC LIMIT 1", symbol.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"Stock data for {symbol} not found")

        # Fetch recent news (example, you might need a dedicated news fetching mechanism)
        # For now, we'll simulate fetching news as part of the prompt
        # In a real scenario, integrate with a news API or scrape news
        news_data = f"No recent news found for {symbol}." # Placeholder

        prompt_data = {
            "symbol": stock_data['symbol'],
            "company_name": stock_data['company_name'],
            "current_price": stock_data['current_price'],
            "volume": stock_data['volume'],
            "pe_ratio": stock_data['pe_ratio'],
            "eps": stock_data['eps'],
            "book_value": stock_data['book_value'],
            "news": news_data
        }

        # Similar to /research, this will block. Consider background tasks for long-running operations.
        research_result = await research_agent.run_deep_research(json.dumps(prompt_data))
        return {"status": "success", "stock_symbol": symbol, "research_report": research_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running stock research for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/trading/signals")
async def get_all_trading_signals(
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None
) -> List[Dict]:
    logger.info(f"Received request for all trading signals: force_refresh={force_refresh}")
    if not trading_agent:
        logger.error("NepseTradingAgent not initialized for /trading/signals endpoint")
        raise HTTPException(status_code=503, detail="Trading agent not available")
    if not pg_conn:
        logger.error("PostgreSQL connection not available for trading signals")
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        # Get all stock symbols
        records = await pg_conn.fetch("SELECT DISTINCT symbol FROM stock_data ORDER BY symbol")
        symbols = [r["symbol"] for r in records]
        
        signals = []
        for symbol in symbols:
            try:
                # Only pass the symbol to the agent, as required by its method signature
                signal = await trading_agent.generate_trading_signal(symbol.upper())
                signals.append({"symbol": symbol, "signal": signal})
            except TradingAgentError as e:
                logger.warning(f"Trading agent error for {symbol}: {e}")
                signals.append({"symbol": symbol, "signal": f"Error: {e}"})
            except Exception as e:
                logger.error(f"Unexpected error generating signal for {symbol}: {e}", exc_info=True)
                signals.append({"symbol": symbol, "signal": f"Internal Error: {e}"})

        return signals
    except Exception as e:
        logger.error(f"Error fetching all trading signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/trading/signal/{symbol}")
async def get_trading_signal_for_stock(
    symbol: str,
    force_refresh: bool = False,
    background_tasks: BackgroundTasks = None
) -> Dict:
    logger.info(f"Received request for trading signal: symbol={symbol}, force_refresh={force_refresh}")
    if not trading_agent:
        logger.error("NepseTradingAgent not initialized for /trading/signal/{symbol} endpoint")
        raise HTTPException(status_code=503, detail="Trading agent not available")
    if not pg_conn:
        logger.error("PostgreSQL connection not available for trading signal")
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        # Fetch recent historical data for analysis
        historical_data = await pg_conn.fetch(
            "SELECT * FROM stock_data WHERE symbol = $1 ORDER BY created_at DESC LIMIT 30",
            symbol.upper()
        )
        if not historical_data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")

        # Only pass the symbol to the agent, as required by its method signature
        signal = await trading_agent.generate_trading_signal(symbol.upper())
        return {"stock_symbol": symbol, "signal": signal}
    except TradingAgentError as e:
        logger.error(f"Trading agent error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Trading agent error: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating trading signal for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@app.get("/test_trading_agent")
async def test_trading_agent() -> Dict:
    """Test if the trading agent is initialized"""
    logger.info("Received request to test trading agent initialization")
    if trading_agent is None:
        logger.warning("Trading agent is not initialized")
        return {"status": "Trading agent is not initialized"}
    logger.info("Trading agent is initialized")
    return {"status": "Trading agent is initialized"}

# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)