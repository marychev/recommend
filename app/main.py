from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.clickhouse import get_clickhouse_client
from app.db.redis_client import get_redis_client
from app.api import events, recommendations, users, tracks, health


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("="*60)
    print("🚀 Запуск приложения Music Recommendation System...")
    print("="*60)

    # Подключение к ClickHouse
    clickhouse_connected = False
    try:
        print(
            f"\n📊 Подключение к ClickHouse "
            f"({settings.clickhouse_host}:{settings.clickhouse_port})..."
        )
        clickhouse = get_clickhouse_client()
        clickhouse.connect()
        clickhouse_connected = True
        print("   ✅ ClickHouse подключен успешно!")
    except Exception as exc:
        print("   ❌ ОШИБКА: Не удалось подключиться к ClickHouse!")
        print(f"   Детали: {exc}")
        print("\n   💡 Решение:")
        print("      docker-compose up -d clickhouse")
        print("      или")
        print("      bash scripts/docker-reset-clickhouse.sh")

    # Подключение к Redis
    redis_connected = False
    try:
        print(
            f"\n🔴 Подключение к Redis "
            f"({settings.redis_host}:{settings.redis_port})..."
        )
        redis = get_redis_client()
        await redis.connect()
        redis_connected = True
        print("   ✅ Redis подключен успешно!")
    except Exception as exc:
        print(f"   ⚠️ Не удалось подключиться к Redis: {exc}")
        print("   💡 Запустите: docker-compose up -d redis")

    print("\n" + "="*60)
    if clickhouse_connected and redis_connected:
        print("✅ Все критичные сервисы подключены!")
    elif clickhouse_connected:
        print("⚠️  Приложение запущено, но Redis недоступен")
    else:
        print("❌ ВНИМАНИЕ: ClickHouse не подключен!")
        print(
            "   API будет возвращать ошибки до подключения к ClickHouse"
        )
    print("="*60)
    print(
        f"\n🌐 API доступен на: "
        f"http://{settings.api_host}:{settings.api_port}"
    )
    print(f"📚 Документация: http://localhost:{settings.api_port}/docs")
    print("="*60 + "\n")

    yield

    # Shutdown
    print("\n" + "="*60)
    print("🛑 Остановка приложения...")
    print("="*60)

    # Отключение от ClickHouse
    try:
        clickhouse = get_clickhouse_client()
        if clickhouse.is_connected():
            clickhouse.disconnect()
    except Exception as exc:
        print(f"⚠️ Ошибка при отключении от ClickHouse: {exc}")

    # Отключение от Redis
    try:
        redis = get_redis_client()
        if await redis.is_connected():
            await redis.disconnect()
    except Exception as exc:
        print(f"⚠️ Ошибка при отключении от Redis: {exc}")

    print("✓ Приложение остановлено")
    print("="*60)


# Создание приложения FastAPI
app = FastAPI(
    title="Music Recommendation System API",
    description="""
API для рекомендательной системы музыкальных композиций.

## Основные возможности:

* **События** - Прием и обработка событий взаимодействия
* **Рекомендации** - Генерация персонализированных рекомендаций
* **Пользователи** - Управление профилями пользователей
* **Треки** - Управление каталогом музыкальных композиций
* **Статистика** - Аналитика по пользователям и трекам

## Технологический стек:

* FastAPI - Web framework
* ClickHouse - OLAP база данных для аналитики
* Kafka - Стриминг событий в реальном времени
* Redis - Кэширование и очереди
* Scikit-learn / Surprise - ML алгоритмы рекомендаций
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    response_model=dict,
    tags=["Root"],
    summary="Корневой эндпоинт",
    description="Возвращает основную информацию об API"
)
async def root():
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
