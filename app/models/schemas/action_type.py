from enum import Enum


class ActionType(str, Enum):
    """Типы действий пользователя с треком"""
    PLAY = "play"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    ADD_TO_PLAYLIST = "add_to_playlist"
    SHARE = "share"
