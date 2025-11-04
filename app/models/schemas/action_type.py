from enum import Enum
from typing import Dict


class ActionType(str, Enum):
    """
    Типы действий пользователя с треком
    
    Каждое действие имеет свой вес для расчета неявного рейтинга
    в системе рекомендаций.
    """
    PLAY = "play"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    ADD_TO_PLAYLIST = "add_to_playlist"
    SHARE = "share"
    
    @property
    def description(self) -> str:
        """Возвращает описание действия на русском языке"""
        descriptions = {
            ActionType.PLAY: "Прослушивание трека",
            ActionType.LIKE: "Лайк трека",
            ActionType.DISLIKE: "Дизлайк трека",
            ActionType.SKIP: "Пропуск трека",
            ActionType.ADD_TO_PLAYLIST: "Добавление в плейлист",
            ActionType.SHARE: "Поделиться треком"
        }
        return descriptions.get(self, "Неизвестное действие")
    
    @property
    def weight(self) -> float:
        """
        Возвращает вес действия для расчета неявного рейтинга
        
        Веса используются в алгоритме Collaborative Filtering
        для построения user-item матрицы.
        """
        weights = {
            ActionType.PLAY: 1.0,
            ActionType.LIKE: 3.0,
            ActionType.DISLIKE: -3.0,
            ActionType.SKIP: -0.5,
            ActionType.ADD_TO_PLAYLIST: 2.0,
            ActionType.SHARE: 2.5
        }
        return weights.get(self, 0.0)
    
    @classmethod
    def get_all_with_info(cls) -> Dict[str, Dict[str, any]]:
        """
        Возвращает словарь всех действий с их описанием и весом
        
        Returns:
            dict: {action_type: {description: str, weight: float}}
        """
        return {
            action.value: {
                "description": action.description,
                "weight": action.weight
            }
            for action in cls
        }
