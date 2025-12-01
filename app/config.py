from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "music_recommend"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_events: str = "user_track_events"
    kafka_consumer_group: str = "recommend_consumer"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # Uvicorn server settings
    api_timeout_keep_alive: int = 65  # Keep-alive timeout в секундах (больше чем у клиентов)
    api_timeout_graceful_shutdown: int = 30  # Graceful shutdown timeout
    api_limit_concurrency: int = 1000  # Максимум одновременных соединений
    api_limit_max_requests: int = 10000  # Максимум запросов на worker перед перезапуском

    # ML Model
    min_interactions_for_recommendations: int = 5
    top_n_recommendations: int = 10
    
    # Cache settings
    recommendations_cache_ttl: int = 3600  # 1 час по умолчанию

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
