"""
Data Service for Business Intelligence Platform
Handles data storage, retrieval, and management operations
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import redis
import sqlite3
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DataRecord:
    """Represents a data record with metadata"""
    id: str
    data_type: str
    content: Dict
    timestamp: datetime
    source: str
    confidence_score: float
    tags: List[str]

class DataService:
    """Service for managing data storage and retrieval"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db_path: str = "data/market_intelligence.db"):
        self.redis_url = redis_url
        self.db_path = db_path
        self.redis_client = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize storage systems"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}")
            self.redis_client = None
        
        # Initialize SQLite database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id TEXT PRIMARY KEY,
                    industry TEXT,
                    data_type TEXT,
                    content TEXT,
                    timestamp TEXT,
                    source TEXT,
                    confidence_score REAL,
                    tags TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id TEXT PRIMARY KEY,
                    industry TEXT,
                    analysis_type TEXT,
                    result_content TEXT,
                    timestamp TEXT,
                    confidence_score REAL,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_data (
                    id TEXT PRIMARY KEY,
                    industry TEXT,
                    metric_name TEXT,
                    value REAL,
                    timestamp TEXT,
                    trend TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
    
    async def store_market_data(self, industry: str, data_type: str, content: Dict, source: str = "unknown") -> str:
        """Store market data with metadata"""
        try:
            record_id = f"{industry}_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            record = DataRecord(
                id=record_id,
                data_type=data_type,
                content=content,
                timestamp=datetime.now(),
                source=source,
                confidence_score=content.get('confidence_score', 0.8),
                tags=content.get('tags', [])
            )
            
            # Store in SQLite
            await self._store_in_database(record, industry)
            
            # Store in Redis for caching
            if self.redis_client:
                await self._store_in_redis(record, industry)
            
            logger.info(f"Stored market data: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Error storing market data: {str(e)}")
            raise
    
    async def _store_in_database(self, record: DataRecord, industry: str):
        """Store record in SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_data 
                (id, industry, data_type, content, timestamp, source, confidence_score, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id,
                industry,
                record.data_type,
                json.dumps(record.content),
                record.timestamp.isoformat(),
                record.source,
                record.confidence_score,
                json.dumps(record.tags)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing in database: {str(e)}")
            raise
    
    async def _store_in_redis(self, record: DataRecord, industry: str):
        """Store record in Redis cache"""
        try:
            if self.redis_client:
                key = f"market_data:{industry}:{record.id}"
                value = json.dumps(asdict(record))
                self.redis_client.setex(key, 3600, value)  # Cache for 1 hour
                
        except Exception as e:
            logger.error(f"Error storing in Redis: {str(e)}")
    
    async def retrieve_market_data(self, industry: str, data_type: str = None, limit: int = 100) -> List[DataRecord]:
        """Retrieve market data for an industry"""
        try:
            # Try Redis first
            if self.redis_client:
                records = await self._retrieve_from_redis(industry, data_type, limit)
                if records:
                    return records
            
            # Fallback to database
            return await self._retrieve_from_database(industry, data_type, limit)
            
        except Exception as e:
            logger.error(f"Error retrieving market data: {str(e)}")
            return []
    
    async def _retrieve_from_redis(self, industry: str, data_type: str = None, limit: int = 100) -> List[DataRecord]:
        """Retrieve records from Redis cache"""
        try:
            if not self.redis_client:
                return []
            
            pattern = f"market_data:{industry}:*"
            if data_type:
                pattern = f"market_data:{industry}:*_{data_type}_*"
            
            keys = self.redis_client.keys(pattern)
            records = []
            
            for key in keys[:limit]:
                value = self.redis_client.get(key)
                if value:
                    data = json.loads(value)
                    record = DataRecord(**data)
                    record.timestamp = datetime.fromisoformat(data['timestamp'])
                    records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving from Redis: {str(e)}")
            return []
    
    async def _retrieve_from_database(self, industry: str, data_type: str = None, limit: int = 100) -> List[DataRecord]:
        """Retrieve records from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT id, data_type, content, timestamp, source, confidence_score, tags
                FROM market_data 
                WHERE industry = ?
            '''
            params = [industry]
            
            if data_type:
                query += " AND data_type = ?"
                params.append(data_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = DataRecord(
                    id=row[0],
                    data_type=row[1],
                    content=json.loads(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    source=row[4],
                    confidence_score=row[5],
                    tags=json.loads(row[6])
                )
                records.append(record)
            
            conn.close()
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving from database: {str(e)}")
            return []
    
    async def store_analysis_result(self, industry: str, analysis_type: str, result: Dict) -> str:
        """Store analysis results"""
        try:
            result_id = f"analysis_{industry}_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO analysis_results 
                (id, industry, analysis_type, result_content, timestamp, confidence_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                result_id,
                industry,
                analysis_type,
                json.dumps(result),
                datetime.now().isoformat(),
                result.get('confidence_score', 0.8),
                json.dumps(result.get('metadata', {}))
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored analysis result: {result_id}")
            return result_id
            
        except Exception as e:
            logger.error(f"Error storing analysis result: {str(e)}")
            raise
    
    async def retrieve_analysis_results(self, industry: str, analysis_type: str = None, limit: int = 50) -> List[Dict]:
        """Retrieve analysis results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = '''
                SELECT result_content, timestamp, confidence_score
                FROM analysis_results 
                WHERE industry = ?
            '''
            params = [industry]
            
            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = json.loads(row[0])
                result['timestamp'] = row[1]
                result['confidence_score'] = row[2]
                results.append(result)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving analysis results: {str(e)}")
            return []
    
    async def store_monitoring_result(self, result: Dict) -> str:
        """Store monitoring results for real-time dashboard"""
        try:
            monitoring_id = f"monitoring_{result.get('industry', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store in Redis for real-time access
            if self.redis_client:
                key = f"monitoring:{result.get('industry', 'unknown')}:latest"
                self.redis_client.setex(key, 1800, json.dumps(result))  # Cache for 30 minutes
            
            # Store metrics in database
            await self._store_monitoring_metrics(result)
            
            logger.info(f"Stored monitoring result: {monitoring_id}")
            return monitoring_id
            
        except Exception as e:
            logger.error(f"Error storing monitoring result: {str(e)}")
            raise
    
    async def _store_monitoring_metrics(self, result: Dict):
        """Store monitoring metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            industry = result.get('industry', 'unknown')
            timestamp = datetime.now().isoformat()
            
            # Store key metrics
            metrics = [
                ('market_growth', result.get('market_insights', [])),
                ('competitive_activity', len(result.get('competitive_analysis', {}))),
                ('trend_count', len(result.get('trend_predictions', []))),
                ('confidence_score', result.get('confidence_score', 0.0))
            ]
            
            for metric_name, value in metrics:
                cursor.execute('''
                    INSERT INTO monitoring_data 
                    (id, industry, metric_name, value, timestamp, trend)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    f"{industry}_{metric_name}_{timestamp}",
                    industry,
                    metric_name,
                    float(value) if isinstance(value, (int, float)) else len(value) if isinstance(value, list) else 0.0,
                    timestamp,
                    'stable'
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing monitoring metrics: {str(e)}")
    
    async def get_latest_monitoring_data(self, industry: str) -> Optional[Dict]:
        """Get latest monitoring data for real-time dashboard"""
        try:
            if self.redis_client:
                key = f"monitoring:{industry}:latest"
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            
            # Fallback to database
            return await self._get_latest_from_database(industry)
            
        except Exception as e:
            logger.error(f"Error getting latest monitoring data: {str(e)}")
            return None
    
    async def _get_latest_from_database(self, industry: str) -> Optional[Dict]:
        """Get latest monitoring data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT result_content, timestamp
                FROM analysis_results 
                WHERE industry = ? AND analysis_type = 'monitoring'
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (industry,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                result = json.loads(row[0])
                result['timestamp'] = row[1]
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest from database: {str(e)}")
            return None
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old market data
            cursor.execute('''
                DELETE FROM market_data 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            # Clean up old analysis results
            cursor.execute('''
                DELETE FROM analysis_results 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            # Clean up old monitoring data
            cursor.execute('''
                DELETE FROM monitoring_data 
                WHERE timestamp < ?
            ''', (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    async def get_data_statistics(self) -> Dict:
        """Get data storage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Market data stats
            cursor.execute('SELECT COUNT(*) FROM market_data')
            stats['total_market_records'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT industry) FROM market_data')
            stats['industries_covered'] = cursor.fetchone()[0]
            
            # Analysis results stats
            cursor.execute('SELECT COUNT(*) FROM analysis_results')
            stats['total_analysis_results'] = cursor.fetchone()[0]
            
            # Monitoring data stats
            cursor.execute('SELECT COUNT(*) FROM monitoring_data')
            stats['total_monitoring_records'] = cursor.fetchone()[0]
            
            conn.close()
            
            # Redis stats
            if self.redis_client:
                stats['redis_keys'] = len(self.redis_client.keys('*'))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting data statistics: {str(e)}")
            return {} 