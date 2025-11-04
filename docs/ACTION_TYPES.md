# 🎯 Типы действий (ActionType)

## Описание

`ActionType` - это enum, определяющий все возможные типы взаимодействий пользователя с треком в системе.

## 📂 Расположение

```
app/models/schemas/action_type.py
```

## 🎨 Структура Enum

```python
from enum import Enum

class ActionType(str, Enum):
    """Типы действий пользователя с треком"""
    PLAY = "play"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    ADD_TO_PLAYLIST = "add_to_playlist"
    SHARE = "share"
```

## 📊 Действия и их веса

| Действие | Значение | Вес | Описание |
|----------|----------|-----|----------|
| `PLAY` | `play` | +1.0 | Прослушивание трека |
| `LIKE` | `like` | +3.0 | Лайк трека |
| `DISLIKE` | `dislike` | -3.0 | Дизлайк трека |
| `SKIP` | `skip` | -0.5 | Пропуск трека |
| `ADD_TO_PLAYLIST` | `add_to_playlist` | +2.0 | Добавление в плейлист |
| `SHARE` | `share` | +2.5 | Поделиться треком |

### Значение весов

Веса используются в алгоритме Collaborative Filtering для расчета **неявного рейтинга** (implicit rating):

```python
implicit_rating = sum(action.weight for action in user_actions)
```

**Положительные веса** (+) — пользователю нравится трек  
**Отрицательные веса** (−) — пользователю не нравится трек  
**Больший вес** — сильнее сигнал предпочтений

## 🔧 Методы

### 1. `description` (property)

Возвращает описание действия на русском языке.

```python
action = ActionType.PLAY
print(action.description)  # "Прослушивание трека"
```

### 2. `weight` (property)

Возвращает вес действия для расчета рейтинга.

```python
action = ActionType.LIKE
print(action.weight)  # 3.0
```

### 3. `get_all_with_info()` (classmethod)

Возвращает словарь всех действий с их информацией.

```python
all_actions = ActionType.get_all_with_info()
# {
#     "play": {"description": "Прослушивание трека", "weight": 1.0},
#     "like": {"description": "Лайк трека", "weight": 3.0},
#     ...
# }
```

## 📡 API Endpoint

### GET `/api/v1/events/action-types`

Возвращает все типы действий с описанием и весами.

**Пример запроса:**
```bash
curl http://localhost:8000/api/v1/events/action-types
```

**Пример ответа:**
```json
{
  "play": {
    "description": "Прослушивание трека",
    "weight": 1.0
  },
  "like": {
    "description": "Лайк трека",
    "weight": 3.0
  },
  "dislike": {
    "description": "Дизлайк трека",
    "weight": -3.0
  },
  "skip": {
    "description": "Пропуск трека",
    "weight": -0.5
  },
  "add_to_playlist": {
    "description": "Добавление в плейлист",
    "weight": 2.0
  },
  "share": {
    "description": "Поделиться треком",
    "weight": 2.5
  }
}
```

## 💻 Использование в коде

### В Pydantic моделях

```python
from app.models.schemas.action_type import ActionType

class UserTrackInteractionCreate(BaseModel):
    user_id: int
    track_id: int
    action_type: ActionType  # ← Используем enum
    listen_duration_seconds: Optional[int] = 0
```

### В API endpoint

```python
from app.models.schemas.action_type import ActionType

@router.post("/events")
async def create_event(event: UserTrackInteractionCreate):
    # Получаем строковое значение
    action_value = event.action_type.value  # "play"
    
    # Получаем описание
    description = event.action_type.description  # "Прослушивание трека"
    
    # Получаем вес
    weight = event.action_type.weight  # 1.0
```

### Валидация

FastAPI автоматически валидирует значения:

```bash
# ✅ Валидное значение
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 1, "action_type": "play"}'

# ❌ Невалидное значение
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "track_id": 1, "action_type": "invalid"}'
# Ответ: 422 Unprocessable Entity
```

### Итерация по всем действиям

```python
# Получить все действия
for action in ActionType:
    print(f"{action.value}: {action.description} (вес: {action.weight})")

# Результат:
# play: Прослушивание трека (вес: 1.0)
# like: Лайк трека (вес: 3.0)
# dislike: Дизлайк трека (вес: -3.0)
# skip: Пропуск трека (вес: -0.5)
# add_to_playlist: Добавление в плейлист (вес: 2.0)
# share: Поделиться треком (вес: 2.5)
```

## 🧮 Расчет неявного рейтинга

В системе рекомендаций используется следующая логика:

```python
def calculate_implicit_rating(user_id: int, track_id: int) -> float:
    """
    Рассчитывает неявный рейтинг трека для пользователя
    на основе всех его действий с этим треком
    """
    actions = get_user_track_actions(user_id, track_id)
    
    rating = 0.0
    for action in actions:
        action_type = ActionType(action.action_type)
        rating += action_type.weight
    
    return rating

# Пример:
# Пользователь:
# - Прослушал трек (play): +1.0
# - Поставил лайк (like): +3.0
# - Добавил в плейлист (add_to_playlist): +2.0
# Итого: 1.0 + 3.0 + 2.0 = 6.0 (высокий рейтинг)
```

## 🎯 Применение в ML алгоритме

### User-Item Matrix

Веса используются для построения матрицы user-item:

```sql
CREATE MATERIALIZED VIEW user_track_matrix AS
SELECT 
    user_id,
    track_id,
    sum(
        CASE action_type
            WHEN 'play' THEN 1.0
            WHEN 'like' THEN 3.0
            WHEN 'dislike' THEN -3.0
            WHEN 'skip' THEN -0.5
            WHEN 'add_to_playlist' THEN 2.0
            WHEN 'share' THEN 2.5
            ELSE 0
        END
    ) as implicit_rating
FROM user_track_interactions
GROUP BY user_id, track_id;
```

### Collaborative Filtering

```python
# 1. Найти похожих пользователей на основе матрицы рейтингов
similar_users = find_similar_users(user_id, based_on="implicit_rating")

# 2. Найти треки, которые понравились похожим пользователям
# (с высоким implicit_rating)
recommended_tracks = get_tracks_from_similar_users(
    similar_users,
    min_rating=2.0  # Только треки с положительным рейтингом
)
```

## 🔄 Добавление нового типа действия

Если нужно добавить новый тип действия:

1. **Добавьте в enum:**
```python
class ActionType(str, Enum):
    # ... существующие ...
    DOWNLOAD = "download"  # Новое действие
```

2. **Добавьте описание:**
```python
@property
def description(self) -> str:
    descriptions = {
        # ... существующие ...
        ActionType.DOWNLOAD: "Скачивание трека",
    }
    return descriptions.get(self, "Неизвестное действие")
```

3. **Добавьте вес:**
```python
@property
def weight(self) -> float:
    weights = {
        # ... существующие ...
        ActionType.DOWNLOAD: 2.5,
    }
    return weights.get(self, 0.0)
```

4. **Обновите SQL схему** (если нужно):
```sql
-- В app/db/clickhouse_schemas.sql
-- Обновите CASE в материализованном представлении
```

5. **Обновите документацию** (этот файл)

## 📝 Best Practices

### ✅ Правильно

```python
# Используйте enum
event = UserTrackInteractionCreate(
    user_id=1,
    track_id=1,
    action_type=ActionType.PLAY
)

# Получайте вес через свойство
weight = event.action_type.weight
```

### ❌ Неправильно

```python
# Не используйте строки напрямую
event = UserTrackInteractionCreate(
    user_id=1,
    track_id=1,
    action_type="play"  # Работает, но теряется автодополнение
)

# Не хардкодите веса
weight = 1.0  # Если изменится в enum, здесь останется старое
```

## 🧪 Тестирование

```python
import pytest
from app.models.schemas.action_type import ActionType

def test_action_type_weights():
    """Проверка весов действий"""
    assert ActionType.PLAY.weight == 1.0
    assert ActionType.LIKE.weight == 3.0
    assert ActionType.DISLIKE.weight == -3.0
    assert ActionType.SKIP.weight == -0.5
    assert ActionType.ADD_TO_PLAYLIST.weight == 2.0
    assert ActionType.SHARE.weight == 2.5

def test_action_type_descriptions():
    """Проверка описаний действий"""
    assert ActionType.PLAY.description == "Прослушивание трека"
    assert ActionType.LIKE.description == "Лайк трека"

def test_get_all_with_info():
    """Проверка получения всей информации"""
    all_info = ActionType.get_all_with_info()
    
    assert "play" in all_info
    assert all_info["play"]["weight"] == 1.0
    assert all_info["play"]["description"] == "Прослушивание трека"
```

## 📚 Связанные документы

- [API Events](/app/api/events.py) - Использование ActionType в API
- [User Track Interaction](/app/models/schemas/user_track_interaction.py) - Модели событий
- [Recommendations](/app/api/recommendations.py) - Использование весов в алгоритме
- [README.md](/README.md) - Общая документация проекта

---

**Создано**: 2025-11-04  
**Последнее обновление**: 2025-11-04

