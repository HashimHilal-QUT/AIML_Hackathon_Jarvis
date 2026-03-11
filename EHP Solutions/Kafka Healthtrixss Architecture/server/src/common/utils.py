import redis
from src.common.config import Config

def get_redis_connection():
    return redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        decode_responses=True
    )
