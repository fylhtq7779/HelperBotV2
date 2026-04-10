from enum import Enum, auto

class UserState(Enum):
    """Состояния пользователя в боте"""
    IDLE = auto()  # Ожидание действий
    WAITING_FOR_DDS = auto()  # Ожидание DDS файла
    WAITING_FOR_SKIN_NAME = auto()  # Ожидание названия скина
    WAITING_FOR_DISPLAY_NAME = auto()  # Ожидание отображаемого названия
    WAITING_FOR_CAR = auto()  # Ожидание выбора машины 