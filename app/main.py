from app.config import settings
from app.app import app
from app.routers import health, users, tracks, events, recommendations, cache_debug


@app.get(
    "/",
    response_model=dict,
    tags=["Root"],
    summary="Корневой эндпоинт",
    description="Возвращает основную информацию об API",
)
async def root() -> dict:
    """Корневой эндпоинт API"""
    return {
        "message": "Music Recommendation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running",
    }


# Подключение роутеров (префиксы и теги уже определены в самих роутерах)
app.include_router(health.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(tracks.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(cache_debug.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        timeout_keep_alive=settings.api_timeout_keep_alive,
        timeout_graceful_shutdown=settings.api_timeout_graceful_shutdown,
        limit_concurrency=settings.api_limit_concurrency,
        limit_max_requests=settings.api_limit_max_requests,
    )
