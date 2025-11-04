"""
Сервисы приложения
"""

from app.services.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    invalidate_user_recommendations,
    get_cache_stats,
)

__all__ = [
    "get_cached_recommendations",
    "set_cached_recommendations",
    "invalidate_user_recommendations",
    "get_cache_stats",
]
