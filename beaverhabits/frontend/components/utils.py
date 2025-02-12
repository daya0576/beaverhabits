import asyncio
import time
from functools import wraps
from typing import Callable, Dict, List, Tuple

from beaverhabits.logging import logger

class RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.timestamps: List[float] = []
        self.lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self.lock:
            now = time.time()
            # Remove timestamps outside the window
            self.timestamps = [ts for ts in self.timestamps if now - ts <= self.window]
            
            if len(self.timestamps) >= self.limit:
                logger.warning(f"Rate limit exceeded: {self.limit} requests in {self.window}s")
                return False
                
            self.timestamps.append(now)
            return True

def ratelimiter(limit: int, window: int):
    """Rate limit decorator for async functions
    
    Args:
        limit: Maximum number of calls allowed in the window
        window: Time window in seconds
    """
    limiters: Dict[Tuple[int, int], RateLimiter] = {}
    
    def decorator(func: Callable):
        # Create or get limiter for this limit/window combo
        key = (limit, window)
        if key not in limiters:
            limiters[key] = RateLimiter(limit, window)
        limiter = limiters[key]
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await limiter.acquire():
                logger.warning(f"Rate limited call to {func.__name__}")
                return
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator
