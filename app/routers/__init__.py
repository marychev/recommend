"""
Централизованный экспорт всех роутеров приложения
"""

from app.routers import health, users, tracks, events, recommendations

__all__ = ["health", "users", "tracks", "events", "recommendations"]
