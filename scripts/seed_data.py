"""
Скрипт для генерации тестовых данных
"""
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.clickhouse import get_clickhouse_client
from app.config import settings
from app.models.schemas import User, Track, UserTrackInteraction


def generate_users(count=100):
    """Генерация тестовых пользователей"""
    print(f"📝 Генерация {count} пользователей...")
    
    clickhouse = get_clickhouse_client()
    
    usernames = [
        "john_doe", "jane_smith", "alex_brown", "maria_garcia", "david_wilson",
        "emma_johnson", "michael_jones", "sarah_davis", "james_martinez", "lisa_anderson"
    ]
    
    countries = ["Russia", "USA", "UK", "Germany", "France", "Spain", "Italy", "Japan", "China"]
    
    users_data = []
    for i in range(1, count + 1):
        username = f"{random.choice(usernames)}_{i}"
        email = f"{username}@example.com"
        age = random.randint(18, 65)
        country = random.choice(countries)
        created_at = datetime.now() - timedelta(days=random.randint(1, 365))
        
        users_data.append([i, username, email, age, country, created_at])
    
    clickhouse.insert(
        "users",
        users_data,
        column_names=User.column_names()
    )
    
    print(f"✅ Создано {count} пользователей")


def generate_tracks(count=500):
    """Генерация тестовых треков"""
    print(f"📝 Генерация {count} треков...")
    
    clickhouse = get_clickhouse_client()
    
    genres = ["Rock", "Pop", "Hip-Hop", "Electronic", "Jazz", "Classical", "Metal", "Indie", "R&B", "Country"]
    
    artists = [
        "The Beatles", "Queen", "Pink Floyd", "Led Zeppelin", "The Rolling Stones",
        "Nirvana", "Radiohead", "Arctic Monkeys", "Metallica", "AC/DC",
        "Daft Punk", "The Strokes", "Red Hot Chili Peppers", "Coldplay", "Muse"
    ]
    
    titles = [
        "Yesterday", "Bohemian Rhapsody", "Stairway to Heaven", "Imagine", "Hotel California",
        "Smells Like Teen Spirit", "Hey Jude", "Sweet Child O' Mine", "Come Together", "Purple Haze",
        "Billie Jean", "Like a Rolling Stone", "What's Going On", "Respect", "Good Vibrations"
    ]
    
    albums = [
        "Abbey Road", "Dark Side of the Moon", "Thriller", "Back in Black", "Rumours",
        "Nevermind", "OK Computer", "The Wall", "Led Zeppelin IV", "Born to Run"
    ]
    
    tracks_data = []
    for i in range(1, count + 1):
        title = f"{random.choice(titles)} {i}"
        artist = random.choice(artists)
        album = random.choice(albums)
        genre = random.choice(genres)
        duration = random.randint(120, 360)
        year = random.randint(1960, 2024)
        created_at = datetime.now() - timedelta(days=random.randint(1, 1000))
        
        tracks_data.append([i, title, artist, album, genre, duration, year, created_at])
    
    clickhouse.insert(
        "tracks",
        tracks_data,
        column_names=Track.column_names(),
    )
    
    print(f"✅ Создано {count} треков")


def generate_interactions(count=10000, user_count=100, track_count=500):
    """Генерация тестовых взаимодействий"""
    print(f"📝 Генерация {count} взаимодействий...")
    
    clickhouse = get_clickhouse_client()
    
    actions = ["play", "like", "dislike", "skip", "add_to_playlist", "share"]
    action_weights = [70, 15, 3, 8, 3, 1]  # Веса для более реалистичного распределения
        
    # Создаем взаимодействия пакетами
    batch_size = 1000
    for batch in range(count // batch_size):
        batch_data = []
        
        for _ in range(batch_size):
            user_id = random.randint(1, user_count)
            track_id = random.randint(1, track_count)
            action = random.choices(actions, weights=action_weights)[0]
            
            # Длительность прослушивания только для play
            listen_duration = random.randint(30, 300) if action == "play" else None
            
            # Случайная дата за последние 90 дней
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            batch_data.append([user_id, track_id, action, listen_duration, timestamp])
        
        clickhouse.insert(
            "user_track_interactions",
            batch_data,
            column_names=UserTrackInteraction.column_names()
        )
        
        print(f"  ✓ Обработано {(batch + 1) * batch_size} / {count}")
    
    print(f"✅ Создано {count} взаимодействий")


def main():
    """Главная функция"""
    print("🚀 Начинаем генерацию тестовых данных...")
    print(f"📊 Подключение к ClickHouse: {settings.clickhouse_host}:{settings.clickhouse_port}")
    
    try:
        # Подключаемся к ClickHouse
        clickhouse = get_clickhouse_client()
        clickhouse.connect()
        
        # Проверяем подключение
        if not clickhouse.is_connected():
            print("❌ Не удалось подключиться к ClickHouse")
            return
        
        print("✅ Подключение установлено\n")
        
        # Генерируем данные
        generate_users(count=100)
        generate_tracks(count=500)
        generate_interactions(count=10000, user_count=100, track_count=500)
        
        print("\n🎉 Генерация данных завершена!")
        print("\n📈 Статистика:")
        
        # Выводим статистику
        users_count = clickhouse.execute("SELECT count() FROM users").result_rows[0][0]
        tracks_count = clickhouse.execute("SELECT count() FROM tracks").result_rows[0][0]
        interactions_count = clickhouse.execute("SELECT count() FROM user_track_interactions").result_rows[0][0]
        
        print(f"  👥 Пользователей: {users_count}")
        print(f"  🎵 Треков: {tracks_count}")
        print(f"  📊 Взаимодействий: {interactions_count}")
        
        # Отключаемся
        clickhouse.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

