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
for router in [
    health.router,
    users.router,
    tracks.router,
    events.router,
    recommendations.router,
    cache_debug.router,
]:
    app.include_router(router, prefix=settings.api_prefix)


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
