"""
Скрипт для генерации тестовых данных с использованием Faker
Генерирует 1,000,000 записей в ClickHouse для нагрузочного тестирования
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from faker import Faker

# Добавляем корневую директорию в PATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.clickhouse import get_clickhouse_client
from app.config import settings

fake = Faker(['ru_RU', 'en_US'])
Faker.seed(42)
random.seed(42)


class DataGenerator:
    """Генератор тестовых данных"""
    
    def __init__(self):
        self.clickhouse = None
        self.user_ids = []
        self.track_ids = []
        
    async def initialize(self):
        """Инициализация подключения к БД"""
        try:
            self.clickhouse = get_clickhouse_client()
            await self.clickhouse.connect()
            print("✓ Подключение к ClickHouse установлено")
        except Exception as e:
            print(f"\n❌ ОШИБКА: Не удалось подключиться к ClickHouse")
            print(f"   Причина: {e}")
            print(f"\n💡 Убедитесь, что сервисы запущены:")
            print(f"   make up")
            print(f"   make db-init")
            raise
        
    async def generate_users(self, count: int = 100000):
        """
        Генерация пользователей
        
        Args:
            count: Количество пользователей для генерации
        """
        print(f"\n📊 Генерация {count:,} пользователей...")
        
        batch_size = 10000
        batches = count // batch_size
        
        for batch in range(batches):
            users_batch = []
            
            for i in range(batch_size):
                user_id = batch * batch_size + i + 1
                self.user_ids.append(user_id)
                
                users_batch.append([
                    user_id,
                    fake.user_name()[:50],
                    fake.email()[:100],
                    random.randint(13, 70),
                    fake.country()[:50],
                    fake.date_time_between(start_date='-2y', end_date='now')
                ])
            
            await self.clickhouse.insert(
                "users",
                users_batch,
                column_names=["user_id", "username", "email", "age", "country", "created_at"]
            )
            
            print(f"  ✓ Batch {batch + 1}/{batches}: {(batch + 1) * batch_size:,} пользователей")
        
        print(f"✓ Создано {count:,} пользователей")
        
    async def generate_tracks(self, count: int = 50000):
        """
        Генерация треков
        
        Args:
            count: Количество треков для генерации
        """
        print(f"\n🎵 Генерация {count:,} треков...")
        
        genres = [
            'Rock', 'Pop', 'Hip-Hop', 'Jazz', 'Classical', 'Electronic', 
            'Country', 'R&B', 'Metal', 'Blues', 'Reggae', 'Folk', 
            'Indie', 'Punk', 'Soul', 'Disco', 'Techno', 'House'
        ]
        
        artists = [fake.name() for _ in range(5000)]
        
        batch_size = 5000
        batches = count // batch_size
        
        for batch in range(batches):
            tracks_batch = []
            
            for i in range(batch_size):
                track_id = batch * batch_size + i + 1
                self.track_ids.append(track_id)
                
                tracks_batch.append([
                    track_id,
                    fake.catch_phrase()[:100],  # title
                    random.choice(artists)[:100],  # artist
                    fake.bs()[:100],  # album
                    random.choice(genres),
                    random.randint(120, 600),  # duration 2-10 min
                    random.randint(1960, 2024),  # release_year
                    fake.date_time_between(start_date='-2y', end_date='now')
                ])
            
            await self.clickhouse.insert(
                "tracks",
                tracks_batch,
                column_names=[
                    "track_id", "title", "artist", "album", "genre",
                    "duration_seconds", "release_year", "created_at"
                ]
            )
            
            print(f"  ✓ Batch {batch + 1}/{batches}: {(batch + 1) * batch_size:,} треков")
        
        print(f"✓ Создано {count:,} треков")
        
    async def generate_interactions(self, count: int = 850000):
        """
        Генерация взаимодействий пользователей с треками
        
        Args:
            count: Количество взаимодействий для генерации
        """
        print(f"\n💫 Генерация {count:,} взаимодействий...")
        
        action_types = ['play', 'like', 'skip', 'add_to_playlist']
        action_weights = [0.6, 0.2, 0.15, 0.05]  # Вероятности действий
        
        batch_size = 10000
        batches = count // batch_size
        
        for batch in range(batches):
            interactions_batch = []
            
            for i in range(batch_size):
                user_id = random.choice(self.user_ids)
                track_id = random.choice(self.track_ids)
                action_type = random.choices(action_types, weights=action_weights)[0]
                
                # Получаем длительность трека (используем случайную из диапазона)
                track_duration = random.randint(120, 600)
                
                # Длительность прослушивания зависит от действия
                if action_type == 'play':
                    listen_duration = random.randint(track_duration // 2, track_duration)
                elif action_type == 'skip':
                    listen_duration = random.randint(5, track_duration // 3)
                else:
                    listen_duration = 0
                
                interactions_batch.append([
                    user_id,
                    track_id,
                    action_type,
                    listen_duration,
                    fake.date_time_between(start_date='-90d', end_date='now')
                ])
            
            await self.clickhouse.insert(
                "user_track_interactions",
                interactions_batch,
                column_names=[
                    "user_id", "track_id", "action_type",
                    "listen_duration_seconds", "timestamp"
                ]
            )
            
            print(f"  ✓ Batch {batch + 1}/{batches}: {(batch + 1) * batch_size:,} взаимодействий")
        
        print(f"✓ Создано {count:,} взаимодействий")
        
    async def get_current_stats(self):
        """Получение текущей статистики БД"""
        print("\n📈 Текущая статистика БД:")
        
        try:
            users_count = await self.clickhouse.execute("SELECT count() FROM users")
            tracks_count = await self.clickhouse.execute("SELECT count() FROM tracks")
            interactions_count = await self.clickhouse.execute(
                "SELECT count() FROM user_track_interactions"
            )
            
            print(f"  • Пользователей: {users_count[0][0]:,}")
            print(f"  • Треков: {tracks_count[0][0]:,}")
            print(f"  • Взаимодействий: {interactions_count[0][0]:,}")
            print(f"  • Всего записей: {(users_count[0][0] + tracks_count[0][0] + interactions_count[0][0]):,}")
        except Exception as e:
            print(f"  ⚠️  Не удалось получить статистику (возможно, таблицы не созданы)")
            print(f"     Ошибка: {e}")
            print(f"\n💡 Создайте таблицы:")
            print(f"   make db-init")
        
    async def generate_all(
        self,
        users_count: int = 100000,
        tracks_count: int = 50000,
        interactions_count: int = 850000
    ):
        """
        Генерация всех данных
        
        Args:
            users_count: Количество пользователей (по умолчанию 100k)
            tracks_count: Количество треков (по умолчанию 50k)
            interactions_count: Количество взаимодействий (по умолчанию 850k)
            
        Total: ~1,000,000 записей
        """
        print("=" * 70)
        print("🚀 ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ ДЛЯ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        start_time = datetime.now()
        
        await self.initialize()
        
        # Проверяем существование таблиц
        print("\n🔍 Проверка таблиц...")
        try:
            await self.clickhouse.execute("SELECT 1 FROM users LIMIT 1")
            await self.clickhouse.execute("SELECT 1 FROM tracks LIMIT 1")
            await self.clickhouse.execute("SELECT 1 FROM user_track_interactions LIMIT 1")
            print("✓ Все необходимые таблицы существуют")
        except Exception as e:
            print(f"\n❌ ОШИБКА: Таблицы не созданы!")
            print(f"   Причина: {e}")
            print(f"\n💡 Создайте таблицы командой:")
            print(f"   make db-init")
            await self.clickhouse.disconnect()
            return
        
        await self.get_current_stats()
        
        # Генерируем данные
        await self.generate_users(users_count)
        await self.generate_tracks(tracks_count)
        await self.generate_interactions(interactions_count)
        
        # Итоговая статистика
        await self.get_current_stats()
        
        elapsed = datetime.now() - start_time
        print(f"\n⏱️  Время выполнения: {elapsed}")
        print("=" * 70)
        print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        print("=" * 70)
        
        # Закрываем соединение
        await self.clickhouse.disconnect()


async def main():
    """Главная функция"""
    generator = DataGenerator()
    
    # Генерируем 1,000,000 записей:
    # - 100,000 пользователей
    # - 50,000 треков
    # - 850,000 взаимодействий
    await generator.generate_all(
        users_count=100000,
        tracks_count=50000,
        interactions_count=850000
    )


if __name__ == "__main__":
    asyncio.run(main())

