"""Pydantic-схемы для валидации входных данных и JSON-ответов."""

from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR = r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"


class HabitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    created_at: datetime


class HabitWithStreak(HabitRead):
    current_streak: int
    done_today: bool


class ToggleRequest(BaseModel):
    """Тело запроса для /habits/{id}/toggle. Если даты нет — берём сегодня."""

    date: date_type | None = None


class ToggleResponse(BaseModel):
    habit_id: int
    date: date_type
    done: bool
    current_streak: int


class HabitData(BaseModel):
    """Данные для отрисовки сетки на фронте."""

    habit_id: int
    name: str
    color: str
    start: date_type
    end: date_type
    current_streak: int
    longest_streak: int
    total: int
    dates: list[date_type]
