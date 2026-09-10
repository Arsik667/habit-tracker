"""Работа с БД: привычки, отметки и расчёт стриков.

Стрик считается на лету при каждом запросе — для single-user приложения
данных мало, кеш не нужен.
"""

from collections.abc import Iterable
from datetime import date as date_type
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import DEFAULT_COLOR, Completion, Habit

# Палитра для новых привычек — берём по кругу, чтобы сетки различались.
PALETTE = ["#4ade80", "#60a5fa", "#f472b6", "#fbbf24", "#a78bfa", "#2dd4bf"]

# Сколько дней показываем в сетке (52 недели + текущая).
GRID_DAYS = 371


# --- привычки -------------------------------------------------------------

def list_habits(db: Session) -> list[Habit]:
    return list(db.scalars(select(Habit).order_by(Habit.created_at, Habit.id)))


def get_habit(db: Session, habit_id: int) -> Habit | None:
    return db.get(Habit, habit_id)


def create_habit(db: Session, name: str, color: str | None = None) -> Habit:
    if color is None:
        color = PALETTE[db.query(Habit).count() % len(PALETTE)]
    habit = Habit(name=name.strip(), color=color or DEFAULT_COLOR)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, habit_id: int) -> bool:
    habit = db.get(Habit, habit_id)
    if habit is None:
        return False
    db.delete(habit)
    db.commit()
    return True


# --- отметки --------------------------------------------------------------

def get_completion_dates(
    db: Session,
    habit_id: int,
    start: date_type | None = None,
    end: date_type | None = None,
) -> set[date_type]:
    stmt = select(Completion.date).where(Completion.habit_id == habit_id)
    if start is not None:
        stmt = stmt.where(Completion.date >= start)
    if end is not None:
        stmt = stmt.where(Completion.date <= end)
    return set(db.scalars(stmt))


def toggle_completion(db: Session, habit_id: int, day: date_type) -> bool:
    """Ставит отметку, если её нет, и снимает, если есть.

    Возвращает True, если после вызова день отмечен.
    """
    existing = db.scalar(
        select(Completion).where(Completion.habit_id == habit_id, Completion.date == day)
    )
    if existing is not None:
        db.execute(delete(Completion).where(Completion.id == existing.id))
        db.commit()
        return False

    db.add(Completion(habit_id=habit_id, date=day))
    db.commit()
    return True


# --- стрики ---------------------------------------------------------------

def calculate_streak(dates: Iterable[date_type], today: date_type | None = None) -> int:
    """Дней подряд к сегодняшнему дню.

    Отсчёт идёт от сегодня, а если сегодня ещё не отмечено — от вчера,
    чтобы стрик не «обнулялся» в течение текущего дня.
    """
    done = set(dates)
    today = today or date_type.today()

    if today in done:
        cursor = today
    elif today - timedelta(days=1) in done:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in done:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak(dates: Iterable[date_type]) -> int:
    """Самая длинная серия за всю историю."""
    ordered = sorted(set(dates))
    if not ordered:
        return 0

    best = current = 1
    for prev, day in zip(ordered, ordered[1:]):
        current = current + 1 if day - prev == timedelta(days=1) else 1
        best = max(best, current)
    return best


def habit_stats(db: Session, habit: Habit, today: date_type | None = None) -> dict:
    """Сводка по привычке для списка на главной."""
    today = today or date_type.today()
    dates = get_completion_dates(db, habit.id)
    return {
        "habit": habit,
        "current_streak": calculate_streak(dates, today),
        "longest_streak": longest_streak(dates),
        "total": len(dates),
        "done_today": today in dates,
    }
