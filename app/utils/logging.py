import logging


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_api_request(
    logger: logging.Logger, method: str, path: str, user_id: int = None
):
    user_info = f" | user_id={user_id}" if user_id else ""
    logger.info(f"{method} {path}{user_info}")


def log_database_query(
    logger: logging.Logger, query: str, execution_time: float = None
):
    query_short = query[:100] + "..." if len(query) > 100 else query
    time_info = f" | {execution_time:.3f}s" if execution_time else ""
    logger.debug(f"DB Query: {query_short}{time_info}")
