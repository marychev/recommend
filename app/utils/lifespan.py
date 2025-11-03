from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.clickhouse import connect_clickhouse, shutdown_clickhouse
from app.db.redis_client import connect_redis, shutdown_redis


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("="*60)
    print("🚀 Запуск приложения Music Recommendation System...")
    print("="*60)

    clickhouse_connected = await connect_clickhouse()
    redis_connected = await connect_redis()

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

    await shutdown_clickhouse()
    await shutdown_redis()
    