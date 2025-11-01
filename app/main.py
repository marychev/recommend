from app.config import settings
from app.app import app
from app.api import events, recommendations, users, tracks, health


@app.get(
    "/",
    response_model=dict,
    tags=["Root"],
    summary="Корневой эндпоинт",
    description="Возвращает основную информацию об API"
)
async def root() -> dict:
    """Корневой эндпоинт API"""
    return {
        "message": "Music Recommendation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }


# Подключение роутеров
app.include_router(
    health.router, prefix="/api/v1", tags=["Health"]
)
app.include_router(
    users.router, prefix="/api/v1", tags=["Users"]
)
app.include_router(
    tracks.router, prefix="/api/v1", tags=["Tracks"]
)
app.include_router(
    events.router, prefix="/api/v1", tags=["Events"]
)
app.include_router(
    recommendations.router, prefix="/api/v1", tags=["Recommendations"]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )
