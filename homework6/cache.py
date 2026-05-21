# cache.py
import json
from redis import Redis

redis_client = Redis(host="localhost", port=6379, db=0, decode_responses=True)

CACHE_TTL = 300  # 5 минут


def get_cache(key: str):
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def set_cache(key: str, value, ttl: int = CACHE_TTL):
    redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))


def delete_cache_by_prefix(prefix: str):
    keys = redis_client.keys(f"{prefix}*")
    if keys:
        redis_client.delete(*keys)


def clear_all_app_cache():
    keys = redis_client.keys("*")
    if keys:
        redis_client.delete(*keys)