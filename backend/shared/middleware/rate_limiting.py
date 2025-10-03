"""
Rate Limiting Middleware
"""

import os
import time
import redis
from flask import request, jsonify, current_app
from functools import wraps


def setup_rate_limiting(app):
    """
    Configure rate limiting middleware
    """
    redis_url = os.getenv("REDIS_URL")

    if redis_url and os.getenv("ENVIRONMENT") != "development":
        try:
            app.redis = redis.from_url(redis_url, decode_responses=True)
            app.logger.info("Redis connection established for rate limiting")
        except Exception as e:
            app.logger.warning(f"Failed to connect to Redis: {e}")
            app.redis = None
    else:
        app.redis = None
        if os.getenv("ENVIRONMENT") == "development":
            app.logger.info("Rate limiting disabled in development mode")
        else:
            app.logger.warning("No Redis URL configured, rate limiting disabled")


class RateLimiter:
    """
    Redis-based rate limiter with sliding window
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(self, key, limit, window_seconds):
        """
        Check if request is allowed under rate limit
        """
        if not self.redis:
            return True  # Allow all requests if Redis unavailable

        try:
            current_time = time.time()
            pipeline = self.redis.pipeline()

            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, current_time - window_seconds)

            # Count current requests
            pipeline.zcard(key)

            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipeline.expire(key, window_seconds)

            results = pipeline.execute()
            current_count = results[1]

            return current_count < limit

        except Exception as e:
            current_app.logger.error(f"Rate limiting error: {e}")
            return True  # Allow request if rate limiting fails


def rate_limit(requests_per_hour=None, requests_per_minute=None):
    """
    Decorator for rate limiting endpoints
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.redis:
                return f(*args, **kwargs)

            # Get rate limits from environment or decorator
            hourly_limit = requests_per_hour or int(
                os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", 1000)
            )
            minute_limit = requests_per_minute or int(
                os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 60)
            )

            # Create rate limiter
            limiter = RateLimiter(current_app.redis)

            # Get client identifier
            client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            user_id = getattr(request, "user_id", None)
            identifier = user_id or client_ip

            # Check hourly limit
            hourly_key = f"rate_limit:hour:{identifier}"
            if not limiter.is_allowed(hourly_key, hourly_limit, 3600):
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {hourly_limit} requests per hour allowed",
                        }
                    ),
                    429,
                )

            # Check minute limit
            minute_key = f"rate_limit:minute:{identifier}"
            if not limiter.is_allowed(minute_key, minute_limit, 60):
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {minute_limit} requests per minute allowed",
                        }
                    ),
                    429,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def api_rate_limit(f):
    """
    Standard API rate limiting decorator
    """
    return rate_limit()(f)
