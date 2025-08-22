import math
from typing import Callable, Optional
from fastapi import Request, HTTPException, Response
from redis.asyncio import Redis
from app.core.redis_client import get_redis

_LUA = """
local key      = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill   = tonumber(ARGV[2])  -- tokens per second
local now_ms   = tonumber(ARGV[3])  -- current time in ms
local cost     = tonumber(ARGV[4])  -- tokens to consume (usually 1)

local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts     = tonumber(data[2])

if tokens == nil then
  tokens = capacity
  ts = now_ms
end

local delta = now_ms - ts
if delta < 0 then delta = 0 end

local add = delta * refill / 1000.0
tokens = math.min(capacity, tokens + add)

local allowed = 0
local retry_after = 0

if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  local need = cost - tokens
  retry_after = math.ceil(need / refill)
end

redis.call('HMSET', key, 'tokens', tokens, 'ts', now_ms)

-- TTL = tid tills hinken blir full igen
local reset = math.ceil((capacity - tokens) / refill)
if reset < 1 then reset = 1 end
redis.call('EXPIRE', key, reset)

return {allowed, tokens, retry_after, reset}
"""

class RateLimiter:
    def __init__(self, redis: Redis):
        self.redis = redis
        self._sha = None
    
    async def _ensure_script(self):
        if not self._sha:
            self._sha = await self.redis.script_load(_LUA)
        
    async def _now_ms(self) -> int:
        # Redis TIME för att undvika klock-skev på flera noder
        sec, usec = await self.redis.time()
        return sec * 1000 + math.floor(usec / 1000)
    
    async def allow(self, key: str, capacity: int, refill_per_sec: float, cost: int = 1):
        await self._ensure_script()
        now_ms = await self._now_ms()
        try:
            allowed, tokens_left, retry_after, reset = await self.redis.evalsha(
                self._sha, 1, key, capacity, refill_per_sec, now_ms, cost
            )
        except Exception:
            allowed, tokens_left, retry_after, reset = await self.redis.eval(
                _LUA, 1, key, capacity, refill_per_sec, now_ms, cost
            )
        return int(allowed), float(tokens_left), int(retry_after), int(reset)

def _headers(resp: Response, limit: int, remaining: int, reset: int):
    resp.headers["X-RateLimit-Limit"] = str(limit) 
    resp.headers["X-RateLimit-Remaining"] = str(max(remaining, 0)) 
    resp.headers["X-RateLimit-Reset"] = str(max(reset, 0))

def rate_limit_dependency(bucket_id: str, capacity: int, refill_per_sec: float, cost_getter: Optional[Callable[[Request], int]] = None, key_from_api_key: bool = True) -> Callable[[Request, Response], None]:
    """
    Skapar en FastAPI-dependency som applicerar token-bucket.
    - bucket_id: t.ex. "odds_post" eller "predictions_post"
    - capacity/refill_per_sec: hinkstorlek och påfyllning (tokens/sek)
    - cost_getter: om du vill debitera >1 token per request (t.ex payload storlek)
    - key_from_api_key: True => per-nyckel; False => global
    """
    limiter = RateLimiter(get_redis())

    async def _dep(request: Request, response: Response):
        api_key = request.headers.get("X-API-Key", "anonymous")
        # Unik nyckel: per API-key eller global
        suffix = api_key if key_from_api_key else "global"
        key = f"rl:{bucket_id}:{suffix}"

        cost = 1
        if cost_getter:
            try:
                cost = max(1, int(cost_getter(request)))
            except Exception:
                cost = 1
        
        allowed, tokens_left, retry_after, reset = await limiter.allow(
            key=key,
            capacity=capacity,
            refill_per_sec=refill_per_sec,
            cost=cost
        )
        _headers(response, capacity, math.floor(tokens_left), reset)

        if not allowed:
            retry = max(1, retry_after)
            raise HTTPException(
                status_code=429,
                detail="rate_limited",
                headers={
                    "Retry-After": str(retry),
                    "X-RateLimit-Limit": str(capacity),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(max(reset, 0)),
                }
            )
    return _dep

async def noop_dependency(request: Request, response: Response):
    return None

def per_key_limiter(bucket_id: str, capacity: int, refill_per_sec: float, cost_getter: Optional[Callable[[Request], int]] = None):
    return rate_limit_dependency(bucket_id, capacity, refill_per_sec, cost_getter,key_from_api_key=True)

def global_limiter(bucket_id: str, capacity: int, refill_per_sec: float, cost_getter: Optional[Callable[[Request], int]] = None):
    return rate_limit_dependency(bucket_id, capacity, refill_per_sec, cost_getter, key_from_api_key=False)