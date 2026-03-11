# api_fetcher.py
import asyncio
import json
import time
import orjson  # pip install orjson for faster JSON processing
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import uvicorn
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Nepse Stock Price Tracker")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class StockPrice(BaseModel):
    symbol: str
    last_price: float
    change: float
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    quantity: Optional[int] = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.price_data: Dict[str, StockPrice] = {}
        self.fetch_task = None
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Start data fetching if not already running
        if not self.fetch_task or self.fetch_task.done():
            self.fetch_task = asyncio.create_task(self.fetch_market_data())
        
        # Send initial data if available
        if self.price_data:
            await websocket.send_json({"type": "data", "data": self.price_data})
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
        # Stop data fetching if no more connections
        if not self.active_connections and self.fetch_task:
            self.fetch_task.cancel()
            self.fetch_task = None
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)
    
    async def fetch_market_data(self):
        """Optimized market data fetching for minimal latency"""
        url = "https://merolagani.com/handlers/webrequesthandler.ashx?type=market_summary"
        
        # Performance tracking
        request_times = []
        processing_times = []
        
        async with aiohttp.ClientSession() as session:
            while self.active_connections:
                fetch_start = time.time()
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            # Use faster orjson for parsing
                            data_bytes = await response.read()
                            data = orjson.loads(data_bytes)
                            
                            process_start = time.time()
                            request_time = process_start - fetch_start
                            request_times.append(request_time)
                            
                            # Process market data with optimizations
                            if data.get("mt") == "ok" and "turnover" in data and "detail" in data["turnover"]:
                                # Pre-allocate dictionary for better memory usage
                                stocks = {}
                                detail_list = data["turnover"]["detail"]
                                
                                # Efficient processing loop
                                for stock in detail_list:
                                    symbol = stock.get("s")
                                    if symbol:
                                        # Directly create dict instead of model conversion
                                        stocks[symbol] = {
                                            "symbol": symbol,
                                            "last_price": float(stock.get("lp", 0)),
                                            "change": float(stock.get("pc", 0)),
                                            "high": float(stock.get("h", 0)) if "h" in stock else None,
                                            "low": float(stock.get("l", 0)) if "l" in stock else None,
                                            "open_price": float(stock.get("op", 0)) if "op" in stock else None,
                                            "quantity": int(stock.get("q", 0)) if "q" in stock else None
                                        }
                                
                                # Update stored data directly
                                self.price_data = stocks
                                
                                # Use orjson for faster serialization
                                message = {"type": "data", "data": stocks}
                                
                                # Broadcast to all clients
                                await self.broadcast(message)
                                
                                process_time = time.time() - process_start
                                processing_times.append(process_time)
                                
                                # Log performance every 100 requests
                                if len(request_times) % 100 == 0:
                                    avg_req = sum(request_times[-100:]) * 1000 / 100
                                    avg_proc = sum(processing_times[-100:]) * 1000 / 100
                                    logger.info(f"Performance: Avg request={avg_req:.2f}ms, Avg processing={avg_proc:.2f}ms")
                        else:
                            logger.error(f"API request failed with status {response.status}")
                
                except Exception as e:
                    logger.error(f"Error fetching market data: {str(e)}")
                
                # Minimal delay between requests
                await asyncio.sleep(0.2)  # 200ms polling rate for low latency


# Create connection manager
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for any client messages
            data = await websocket.receive_text()
            # We could process client messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Define a simple HTTP endpoint to check if API is up
@app.get("/")
async def root():
    return {"status": "ok", "message": "Nepse Market Data WebSocket API is running"}

if __name__ == "__main__":
    uvicorn.run("api_fetcher:app", host="0.0.0.0", port=8000, reload=True)