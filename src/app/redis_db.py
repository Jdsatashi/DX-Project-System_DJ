import redis

from utils.env import REDIS_URL

redis_db = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def verify_deactivate_key(user_id: str):
    return f"otp_deactivate:{user_id}"
