"""
Kafka Producer для отправки событий
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from aiokafka.errors import KafkaError

from app.kafka.client import get_kafka_producer
from app.config import settings

logger = logging.getLogger(__name__)


def serialize_event(event: Dict[str, Any]) -> bytes:
    """
    Сериализовать событие в JSON байты
    
    Args:
        event: Словарь события
    
    Returns:
        bytes: Сериализованное событие
    """
    # Конвертируем datetime в ISO string
    if 'timestamp' in event and isinstance(event['timestamp'], datetime):
        event['timestamp'] = event['timestamp'].isoformat()
    
    return json.dumps(event, ensure_ascii=False).encode('utf-8')


async def send_event(event: Dict[str, Any]) -> bool:
    """
    Отправить событие в Kafka
    
    Args:
        event: Словарь с данными события
            - user_id: int
            - track_id: int
            - action_type: str
            - listen_duration_seconds: int
            - timestamp: datetime
    
    Returns:
        bool: True если успешно отправлено
    """
    try:
        producer = await get_kafka_producer()
        
        # Сериализуем событие
        message = serialize_event(event)
        
        # Используем user_id как ключ для партиционирования
        key = str(event.get('user_id', '')).encode('utf-8')
        
        # Отправляем событие
        await producer.send(
            settings.kafka_topic_events,
            value=message,
            key=key
        )
        
        logger.debug(
            f"📨 Событие отправлено в Kafka: "
            f"user={event.get('user_id')}, "
            f"track={event.get('track_id')}, "
            f"action={event.get('action_type')}"
        )
        
        return True
        
    except KafkaError as e:
        logger.error(
            f"❌ Ошибка отправки события в Kafka: {e}",
            extra={"event": event}
        )
        return False
    except Exception as e:
        logger.error(
            f"❌ Неожиданная ошибка при отправке в Kafka: {e}",
            extra={"event": event}
        )
        return False


async def send_batch_events(events: list[Dict[str, Any]]) -> int:
    """
    Отправить пакет событий в Kafka
    
    Args:
        events: Список словарей событий
    
    Returns:
        int: Количество успешно отправленных событий
    """
    success_count = 0
    
    try:
        producer = await get_kafka_producer()
        
        # Создаем batch
        batch = producer.create_batch()
        
        for event in events:
            message = serialize_event(event)
            key = str(event.get('user_id', '')).encode('utf-8')
            
            # Добавляем в batch
            metadata = batch.append(
                key=key,
                value=message,
                timestamp=None
            )
            
            if metadata is None:
                # Batch полон, отправляем
                await producer.send_batch(
                    batch,
                    settings.kafka_topic_events,
                    partition=0
                )
                success_count += len(batch)
                
                # Создаем новый batch
                batch = producer.create_batch()
                batch.append(key=key, value=message, timestamp=None)
        
        # Отправляем оставшиеся события
        if len(batch) > 0:
            await producer.send_batch(
                batch,
                settings.kafka_topic_events,
                partition=0
            )
            success_count += len(batch)
        
        logger.info(
            f"📨 Batch событий отправлен в Kafka: "
            f"{success_count} событий"
        )
        
        return success_count
        
    except KafkaError as e:
        logger.error(f"❌ Ошибка отправки batch в Kafka: {e}")
        return success_count
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при отправке batch: {e}")
        return success_count

