import asyncio
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable

def ratelimiter(limit: int, window: int):
    """Rate limit decorator for async functions.
    
    Args:
        limit: Maximum number of calls allowed within window
        window: Time window in seconds
    """
    if window <= 0 or window > 60 * 60:
        raise ValueError("Window must be between 0 and 3600 seconds")

    # Track calls per function
    calls = defaultdict(list)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            
            # Clean old calls outside window
            calls[func.__name__] = [t for t in calls[func.__name__] if now - t <= window]
            
            # Check if under limit
            if len(calls[func.__name__]) >= limit:
                # Rate limited - delay execution
                await asyncio.sleep(0.1)
                return None
                
            # Add call and execute
            calls[func.__name__].append(now)
            return await func(*args, **kwargs)
            
        return wrapper
    return decorator
