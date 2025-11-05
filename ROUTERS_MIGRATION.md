# Миграция на структуру routers (FastAPI Best Practices)

## 🎯 Что изменилось

Проект реорганизован согласно best practices FastAPI:
- ❌ Старая структура: `app/api/` 
- ✅ Новая структура: `app/routers/`

## 📁 Новая структура

```
app/
├── routers/
│   ├── __init__.py           # Централизованный экспорт роутеров
│   ├── health.py             # Проверка состояния сервиса
│   ├── users.py              # Управление пользователями
│   ├── tracks.py             # Управление треками
│   ├── events.py             # События взаимодействий
│   └── recommendations.py    # Генерация рекомендаций
└── main.py                   # Подключение роутеров
```

## ✨ Преимущества новой структуры

### 1. **Инкапсуляция префиксов и тегов**
Теперь каждый роутер определяет свои префиксы и теги внутри себя:

```python
# app/routers/users.py
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("")  # -> /api/v1/users
async def list_users(): ...

@router.get("/{user_id}")  # -> /api/v1/users/{user_id}
async def get_user(): ...
```

### 2. **Упрощение main.py**
```python
# Было:
app.include_router(users.router, prefix="/api/v1", tags=["Users"])

# Стало:
app.include_router(users.router, prefix="/api/v1")
```

### 3. **Централизованный экспорт**
```python
# app/routers/__init__.py
from app.routers import health, users, tracks, events, recommendations

__all__ = ["health", "users", "tracks", "events", "recommendations"]
```

### 4. **Более чистые URL**
```python
# Было:
@router.get("/users")           # /api/v1/users
@router.get("/users/{user_id}") # /api/v1/users/{user_id}

# Стало:
@router.get("")                 # /api/v1/users
@router.get("/{user_id}")       # /api/v1/users/{user_id}
```

## 🔗 API эндпоинты (не изменились)

Все эндпоинты остались прежними:

### Health
- `GET /api/v1/health` - Проверка состояния сервиса

### Users
- `POST /api/v1/users` - Создать пользователя
- `GET /api/v1/users` - Список пользователей
- `GET /api/v1/users/{user_id}` - Получить пользователя
- `GET /api/v1/users/{user_id}/statistics` - Статистика пользователя

### Tracks
- `POST /api/v1/tracks` - Создать трек
- `GET /api/v1/tracks` - Список треков
- `GET /api/v1/tracks/{track_id}` - Получить трек
- `GET /api/v1/tracks/{track_id}/statistics` - Статистика трека
- `GET /api/v1/tracks/popular/top` - Популярные треки

### Events
- `POST /api/v1/events` - Отправить событие
- `GET /api/v1/events/user/{user_id}` - История событий пользователя
- `GET /api/v1/events/track/{track_id}` - История событий трека
- `GET /api/v1/events/action-types` - Получить типы действий

### Recommendations
- `POST /api/v1/recommendations` - Получить рекомендации (POST)
- `GET /api/v1/recommendations/{user_id}` - Получить рекомендации (GET)

## 🚀 Что делать дальше

### Опциональные улучшения:

1. **Создать `app/routers/dependencies.py`** для общих зависимостей:
```python
# app/routers/dependencies.py
from fastapi import Depends, HTTPException, status
from app.db.clickhouse import get_clickhouse_client

async def get_db():
    """Зависимость для получения подключения к БД"""
    return get_clickhouse_client()

async def verify_user_exists(user_id: int, db = Depends(get_db)):
    """Проверка существования пользователя"""
    result = await db.execute_raw(
        f"SELECT count() FROM users WHERE user_id = {user_id}"
    )
    if result[0][0] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return user_id
```

2. **Добавить версионирование API**:
```python
# app/routers/v1/__init__.py
# app/routers/v2/__init__.py
```

3. **Вынести общие response_models**:
```python
# app/routers/responses.py
from app.models.schemas import User, Track

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
```

## 📚 Ссылки

- [FastAPI Best Practices - Project Structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [APIRouter Documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/#apirouter)

