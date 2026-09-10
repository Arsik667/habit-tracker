"""SQLAlchemy-модели: привычка и отметка о выполнении."""

from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

DEFAULT_COLOR = "#4ade80"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default=DEFAULT_COLOR)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    # cascade без passive_deletes: отметки удаляет сам ORM, поэтому история
    # чистится даже если внешние ключи в БД отключены.
    completions: Mapped[list["Completion"]] = relationship(
        back_populates="habit",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Habit id={self.id} name={self.name!r}>"


class Completion(Base):
    __tablename__ = "completions"
    # Одна отметка на привычку в день — защита от дублей на уровне БД.
    __table_args__ = (UniqueConstraint("habit_id", "date", name="uq_completion_habit_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    habit: Mapped["Habit"] = relationship(back_populates="completions")

    def __repr__(self) -> str:
        return f"<Completion habit_id={self.habit_id} date={self.date}>"
