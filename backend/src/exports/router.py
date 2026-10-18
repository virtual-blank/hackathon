import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from src.auth.deps import CurrentUserDep, SessionDep
from src.exports.schemas import ExportDelimiter
from src.exports.service import ExportsService

router = APIRouter(prefix="/exports", tags=["📥 Exports"])

CSV_RESPONSE_SPEC = {
    200: {
        "content": {
            "text/csv": {
                "schema": {"type": "string", "format": "binary"},
            }
        },
        "description": "CSV-файл со статистикой (UTF-8 с BOM для совместимости с Excel)",
    }
}


@router.get(
    "/habits/summary.csv",
    response_class=Response,
    responses=CSV_RESPONSE_SPEC,
    status_code=status.HTTP_200_OK,
    summary="Export summary statistics on habits to CSV",
    description=(
        "Скачивает .csv файл со сводной аналитикой по всем привычкам текущего пользователя: "
        "количество дней, процент выполнения, текущие и рекордные стрики, статус заброшенности и реакции друзей"
    ),
)
async def export_habits_summary(
    current_user: CurrentUserDep,
    session: SessionDep,
    delimiter: ExportDelimiter = Query(
        default=ExportDelimiter.COMMA,
        description="Разделитель колонок CSV (`,` - стандартный, `;` - для русскоязычного Excel)",
    ),
) -> Response:
    service = ExportsService(session=session)
    csv_content, filename = await service.export_habits_summary_csv(
        user=current_user,
        delimiter=delimiter,
    )
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.get(
    "/habits/logs.csv",
    response_class=Response,
    responses=CSV_RESPONSE_SPEC,
    status_code=status.HTTP_200_OK,
    summary="Экспорт истории выполнений (логов) в CSV",
    description=(
        "Скачивает CSV-файл с хронологическим журналом всех отметок выполнения привычек. "
        "Поддерживает фильтрацию по диапазону дат (`date_from`, `date_to`) и конкретной привычке (`habit_id`)."
    ),
)
async def export_habit_logs(
    current_user: CurrentUserDep,
    session: SessionDep,
    date_from: date | None = Query(default=None, description="Начальная дата (включительно)"),
    date_to: date | None = Query(default=None, description="Конечная дата (включительно)"),
    habit_id: uuid.UUID | None = Query(default=None, description="Фильтр по ID конкретной привычки"),
    delimiter: ExportDelimiter = Query(
        default=ExportDelimiter.COMMA,
        description="Разделитель колонок CSV (`,` или `;`)",
    ),
) -> Response:
    service = ExportsService(session=session)
    try:
        csv_content, filename = await service.export_habit_logs_csv(
            user=current_user,
            date_from=date_from,
            date_to=date_to,
            habit_id=habit_id,
            delimiter=delimiter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
