"""FastAPI-приложение: HTML-страницы + JSON API трекера привычек."""

from contextlib import asynccontextmanager
from datetime import date as date_type
from datetime import timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import crud
from .database import Base, engine, get_db
from .schemas import HabitCreate, HabitData, HabitRead, ToggleRequest, ToggleResponse

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Для мини-проекта хватает create_all вместо миграций.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Habit Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def grid_range(today: date_type) -> tuple[date_type, date_type]:
    """Начало и конец сетки: ~52 недели, выровненные по понедельникам."""
    start = today - timedelta(days=crud.GRID_DAYS - 1)
    return start - timedelta(days=start.weekday()), today


def wants_json(request: Request) -> bool:
    return request.headers.get("content-type", "").startswith("application/json")


# --- страницы -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    today = date_type.today()
    stats = [crud.habit_stats(db, habit, today) for habit in crud.list_habits(db)]
    pending = [s["habit"].name for s in stats if not s["done_today"]]
    return templates.TemplateResponse(
        request,
        "index.html",
        {"stats": stats, "today": today, "pending": pending},
    )


@app.get("/habits/{habit_id}", response_class=HTMLResponse)
def habit_page(habit_id: int, request: Request, db: Session = Depends(get_db)):
    habit = crud.get_habit(db, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Привычка не найдена")

    today = date_type.today()
    stats = crud.habit_stats(db, habit, today)
    return templates.TemplateResponse(
        request,
        "habit.html",
        {"habit": habit, "stats": stats, "today": today},
    )


# --- API ------------------------------------------------------------------

@app.post("/habits", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
async def create_habit(request: Request, db: Session = Depends(get_db)):
    """Создать привычку. Принимает и JSON, и данные HTML-формы."""
    if wants_json(request):
        try:
            payload = HabitCreate.model_validate(await request.json())
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors()) from exc
        habit = crud.create_habit(db, payload.name, payload.color)
        return habit

    form = await request.form()
    name = str(form.get("name") or "").strip()
    if not name:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    color = str(form.get("color") or "") or None
    crud.create_habit(db, name, color)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/habits/{habit_id}/toggle", response_model=ToggleResponse)
def toggle_habit(
    habit_id: int,
    payload: ToggleRequest | None = None,
    db: Session = Depends(get_db),
):
    """Отметить/снять отметку. Без тела запроса — за сегодня."""
    habit = crud.get_habit(db, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Привычка не найдена")

    today = date_type.today()
    day = (payload.date if payload else None) or today
    if day > today:
        raise HTTPException(status_code=400, detail="Нельзя отметить будущую дату")

    done = crud.toggle_completion(db, habit_id, day)
    dates = crud.get_completion_dates(db, habit_id)
    return ToggleResponse(
        habit_id=habit_id,
        date=day,
        done=done,
        current_streak=crud.calculate_streak(dates, today),
    )


@app.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_habit(habit_id: int, db: Session = Depends(get_db)):
    if not crud.delete_habit(db, habit_id):
        raise HTTPException(status_code=404, detail="Привычка не найдена")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/habits/{habit_id}/data", response_model=HabitData)
def habit_data(habit_id: int, db: Session = Depends(get_db)):
    """Даты выполнения за последний год — из этого фронт рисует сетку."""
    habit = crud.get_habit(db, habit_id)
    if habit is None:
        raise HTTPException(status_code=404, detail="Привычка не найдена")

    today = date_type.today()
    start, end = grid_range(today)
    all_dates = crud.get_completion_dates(db, habit_id)
    window = sorted(d for d in all_dates if start <= d <= end)

    return HabitData(
        habit_id=habit.id,
        name=habit.name,
        color=habit.color,
        start=start,
        end=end,
        current_streak=crud.calculate_streak(all_dates, today),
        longest_streak=crud.longest_streak(all_dates),
        total=len(all_dates),
        dates=window,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """404 на странице показываем HTML, в API — обычный JSON."""
    if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, "404.html", {"detail": exc.detail}, status_code=404
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
