import redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)
def clear_trek_cache():
    keys = redis_client.keys("treks:*")

    if keys:
        redis_client.delete(*keys)
