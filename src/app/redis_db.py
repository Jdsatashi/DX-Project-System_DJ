import redis

from utils.env import REDIS_URL

redis_db = redis.Redis.from_url(REDIS_URL, decode_responses=True)
