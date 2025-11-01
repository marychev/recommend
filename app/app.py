from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.helpers.lifespan import lifespan 


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

