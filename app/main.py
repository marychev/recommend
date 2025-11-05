from app.config import settings
from app.app import app
from app.routers import health, users, tracks, events, recommendations


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
