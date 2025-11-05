# API Роутеры (FastAPI Best Practices)

## 📂 Структура

```
routers/
├── __init__.py           # Централизованный экспорт
├── health.py             # /api/v1/health
├── users.py              # /api/v1/users
├── tracks.py             # /api/v1/tracks
├── events.py             # /api/v1/events
└── recommendations.py    # /api/v1/recommendations
```

## ✨ Особенности

### 1. Префиксы и теги определены в роутерах

```python
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)
```

### 2. Чистые пути в декораторах

```python
@router.get("")              # -> /api/v1/users
@router.get("/{user_id}")    # -> /api/v1/users/{user_id}
```

### 3. Swagger документация с примерами

Каждый эндпоинт имеет:
- ✅ `summary` - краткое описание
- ✅ `description` - подробное описание
- ✅ `response_model` - модель ответа
- ✅ Примеры в docstring

## 🎯 Принципы

1. **Один файл = одна сущность** (users, tracks, events)
2. **Все пути относительны** префиксу роутера
3. **Swagger автоматически группирует** по тегам
4. **Централизованный импорт** через `__init__.py`

## 🔍 Пример добавления нового роутера

```python
# app/routers/playlists.py
from fastapi import APIRouter

router = APIRouter(
    prefix="/playlists",
    tags=["Playlists"],
)

@router.get("")
async def list_playlists():
    """Список плейлистов"""
    return []

@router.post("")
async def create_playlist():
    """Создать плейлист"""
    return {}
```

Затем добавить в `app/routers/__init__.py`:
```python
from app.routers import playlists
__all__ = [..., "playlists"]
```

И в `app/main.py`:
```python
from app.routers import playlists
app.include_router(playlists.router, prefix="/api/v1")
```

## 📚 Документация

После запуска сервиса:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

