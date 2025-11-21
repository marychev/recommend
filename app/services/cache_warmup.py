"""
Сервис предварительного прогрева кэша рекомендаций
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.db.clickhouse import get_clickhouse_client
from app.services.cache import set_cached_recommendations
from app.routers.recommendations import get_recommendations
from app.models.schemas import RecommendationRequest
from app.config import settings

logger = logging.getLogger(__name__)


class CacheWarmupService:
    """Сервис для предварительного прогрева кэша рекомендаций"""
    
    def __init__(self):
        self.is_running = False
        self.warmup_stats = {
            "last_run": None,
            "users_warmed": 0,
            "total_time_seconds": 0,
            "errors": 0
        }
    
    async def get_active_users(self, 
                              hours_back: int = 24, 
                              min_interactions: int = 3,
                              limit: int = 100) -> List[int]:
        """
        Получить список активных пользователей для прогрева кэша
        
        Args:
            hours_back: За сколько часов назад смотреть активность
            min_interactions: Минимальное количество взаимодействий
            limit: Максимальное количество пользователей
            
        Returns:
            List[int]: Список ID активных пользователей
        """
        clickhouse = get_clickhouse_client()
        
        try:
            # Запрос активных пользователей за последние N часов
            query = f"""
            SELECT 
                user_id,
                count() as interaction_count,
                max(timestamp) as last_activity
            FROM user_track_interactions 
            WHERE timestamp >= now() - INTERVAL {hours_back} HOUR
            GROUP BY user_id
            HAVING interaction_count >= {min_interactions}
            ORDER BY interaction_count DESC, last_activity DESC
            LIMIT {limit}
            """
            
            result = await clickhouse.execute(query)
            active_users = [row[0] for row in result]
            
            logger.info(
                f"Найдено {len(active_users)} активных пользователей "
                f"(за {hours_back}ч, мин. {min_interactions} взаимодействий)"
            )
            
            return active_users
            
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return []
    
    async def warmup_user_recommendations(self, 
                                        user_id: int,
                                        variants: List[Dict[str, Any]] = None) -> bool:
        """
        Прогрев рекомендаций для конкретного пользователя
        
        Args:
            user_id: ID пользователя
            variants: Варианты параметров для прогрева
            
        Returns:
            bool: True если прогрев успешен
        """
        if variants is None:
            # Стандартные варианты прогрева
            variants = [
                {"top_n": 10, "exclude_listened": True},
                {"top_n": 20, "exclude_listened": True},
                {"top_n": 10, "exclude_listened": False},
            ]
        
        success_count = 0
        
        for variant in variants:
            try:
                # Создаем запрос рекомендаций
                request = RecommendationRequest(
                    user_id=user_id,
                    top_n=variant.get("top_n", 10),
                    exclude_listened=variant.get("exclude_listened", True),
                    include_performance_metrics=False  # Не нужны метрики для прогрева
                )
                
                # Генерируем рекомендации (это автоматически сохранит их в кэш)
                response = await get_recommendations(request)
                
                if response and response.recommendations:
                    success_count += 1
                    logger.debug(
                        f"Прогрев для пользователя {user_id}: "
                        f"top_n={variant['top_n']}, exclude={variant['exclude_listened']} - успешно"
                    )
                else:
                    logger.warning(
                        f"Прогрев для пользователя {user_id}: "
                        f"top_n={variant['top_n']} - пустой результат"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Ошибка прогрева для пользователя {user_id} "
                    f"(top_n={variant.get('top_n', 10)}): {e}"
                )
        
        return success_count > 0
    
    async def warmup_cache_batch(self, 
                               user_ids: List[int],
                               batch_size: int = 10,
                               delay_between_batches: float = 1.0) -> Dict[str, Any]:
        """
        Пакетный прогрев кэша для списка пользователей
        
        Args:
            user_ids: Список ID пользователей
            batch_size: Размер пакета для параллельной обработки
            delay_between_batches: Задержка между пакетами (секунды)
            
        Returns:
            Dict[str, Any]: Статистика прогрева
        """
        start_time = datetime.now()
        total_users = len(user_ids)
        successful_warmups = 0
        errors = 0
        
        logger.info(f"Начинаем пакетный прогрев кэша для {total_users} пользователей")
        
        # Обрабатываем пользователей пакетами
        for i in range(0, total_users, batch_size):
            batch = user_ids[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_users + batch_size - 1) // batch_size
            
            logger.info(f"Обработка пакета {batch_num}/{total_batches} ({len(batch)} пользователей)")
            
            # Параллельный прогрев пакета
            tasks = [self.warmup_user_recommendations(user_id) for user_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Подсчитываем результаты пакета
            for result in batch_results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.error(f"Ошибка в пакете: {result}")
                elif result:
                    successful_warmups += 1
                else:
                    errors += 1
            
            # Задержка между пакетами (чтобы не перегружать систему)
            if i + batch_size < total_users and delay_between_batches > 0:
                await asyncio.sleep(delay_between_batches)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Обновляем статистику
        self.warmup_stats.update({
            "last_run": end_time,
            "users_warmed": successful_warmups,
            "total_time_seconds": total_time,
            "errors": errors
        })
        
        logger.info(
            f"Прогрев завершен: {successful_warmups}/{total_users} пользователей "
            f"за {total_time:.1f}с (ошибок: {errors})"
        )
        
        return {
            "total_users": total_users,
            "successful_warmups": successful_warmups,
            "errors": errors,
            "total_time_seconds": total_time,
            "users_per_second": successful_warmups / total_time if total_time > 0 else 0,
            "success_rate": (successful_warmups / total_users * 100) if total_users > 0 else 0
        }
    
    async def auto_warmup(self, 
                         max_users: int = 50,
                         min_interactions: int = 5) -> Dict[str, Any]:
        """
        Автоматический прогрев кэша для активных пользователей
        
        Args:
            max_users: Максимальное количество пользователей для прогрева
            min_interactions: Минимальное количество взаимодействий
            
        Returns:
            Dict[str, Any]: Результаты прогрева
        """
        if self.is_running:
            return {
                "error": "Прогрев уже выполняется",
                "is_running": True
            }
        
        self.is_running = True
        
        try:
            # Получаем активных пользователей
            active_users = await self.get_active_users(
                hours_back=24,
                min_interactions=min_interactions,
                limit=max_users
            )
            
            if not active_users:
                return {
                    "message": "Не найдено активных пользователей для прогрева",
                    "total_users": 0
                }
            
            # Выполняем прогрев
            result = await self.warmup_cache_batch(active_users)
            
            return {
                "success": True,
                "message": f"Прогрев выполнен для {result['successful_warmups']} пользователей",
                **result
            }
            
        except Exception as e:
            logger.error(f"Ошибка автоматического прогрева: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    def get_warmup_stats(self) -> Dict[str, Any]:
        """Получить статистику прогрева"""
        return {
            "is_running": self.is_running,
            "stats": self.warmup_stats.copy()
        }


# Глобальный экземпляр сервиса
warmup_service = CacheWarmupService()


def get_warmup_service() -> CacheWarmupService:
    """Получить экземпляр сервиса прогрева"""
    return warmup_service
