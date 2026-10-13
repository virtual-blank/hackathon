"""
ORM-моделей для аналитики нет и не должно быть.

Все агрегаты живут в materialized views (mv_habit_dashboard,
mv_habit_streaks, mv_habit_daily), которые создаются миграциями Alembic
и читаются через raw SQL в repository.py.

Базовые модели (Habit, HabitLog, SharedHabitUser) — в src/habits/models.py.
"""
