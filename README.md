# 🔥 Трекер привычек

Мини-приложение на FastAPI: отмечаешь привычки по дням, серия (streak) считается
автоматически, история рисуется сеткой в стиле GitHub contribution graph.

## Стек

FastAPI + SQLAlchemy 2.0 + SQLite, Jinja2-шаблоны, vanilla JS, чистый CSS.
Без авторизации — приложение на одного пользователя.

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Приложение: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs

База `habit_tracker.db` создаётся сама при первом старте.

## API

| Метод  | Путь                  | Что делает                                       |
|--------|-----------------------|--------------------------------------------------|
| GET    | `/`                   | список привычек с текущей серией                 |
| POST   | `/habits`             | создать привычку (HTML-форма или JSON)           |
| GET    | `/habits/{id}`        | страница привычки с сеткой за год                |
| POST   | `/habits/{id}/toggle` | отметить/снять отметку (без тела — за сегодня)   |
| DELETE | `/habits/{id}`        | удалить привычку вместе с историей               |
| GET    | `/habits/{id}/data`   | JSON с датами выполнения за год                  |

Примеры:

```bash
curl -X POST localhost:8000/habits -H 'Content-Type: application/json' -d '{"name":"Чтение"}'
curl -X POST localhost:8000/habits/1/toggle
curl -X POST localhost:8000/habits/1/toggle -H 'Content-Type: application/json' -d '{"date":"2026-09-09"}'
```

## Как считается серия

От сегодняшнего дня идём назад, пока дни отмечены без пропусков. Если сегодня
ещё не отмечено — отсчёт начинается со вчера, чтобы серия не обнулялась в течение
дня. Считается на лету при каждом запросе, без кеша.

## Структура

```
app/
├── main.py       # роуты FastAPI
├── models.py     # Habit, Completion
├── database.py   # движок и сессии
├── schemas.py    # Pydantic-схемы
├── crud.py       # работа с БД + расчёт серий
├── templates/    # base, index, habit, 404
└── static/       # style.css
```
