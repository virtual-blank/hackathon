import uuid
import logging
from fastapi import APIRouter, HTTPException, Query, status

from src.auth.deps import CurrentUserIdDep, SessionDep
from src.feed.schemas import FeedOutputSchema, ReviewCreateSchema, ReviewOutputSchema, ReviewUpdateSchema
from src.feed.service import FeedService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/feed", tags=["👁‍🗨 Feed"])


# == GET FEED ==
@router.get("", response_model=list[FeedOutputSchema], status_code=status.HTTP_200_OK, description="Get feed")
async def get_feed(
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=100, description="Количество постов на странице"),
    offset: int = Query(default=0, ge=0),
):
    service = FeedService(session=session)
    try:
        return await service.get_feed(user_id=current_user_id, limit=limit, offset=offset)
    except Exception:
        logger.exception("Не удалось получить ленту")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == CREATE REVIEW ==
@router.post(
    "/reviews", response_model=ReviewOutputSchema, status_code=status.HTTP_201_CREATED, description="Create new review"
)
async def create_review(current_user_id: CurrentUserIdDep, session: SessionDep, review_dto: ReviewCreateSchema):
    service = FeedService(session=session)
    try:
        return await service.create_review(user_id=current_user_id, review_dto=review_dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        logger.exception("Не удалось создать отзыв")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == EDIT REVIEW ==
@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewOutputSchema,
    status_code=status.HTTP_200_OK,
    description="Edit review",
)
async def edit_review(
    current_user_id: CurrentUserIdDep, review_id: uuid.UUID, session: SessionDep, review_update_dto: ReviewUpdateSchema
):
    service = FeedService(session=session)
    try:
        return await service.edit_review(
            user_id=current_user_id, review_id=review_id, review_update_dto=review_update_dto
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        logger.exception("Не удалось изменить отзыв")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == DELETE REVIEW ==
@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT, description="Delete review")
async def delete_review(current_user_id: CurrentUserIdDep, session: SessionDep, review_id: uuid.UUID) -> None:
    service = FeedService(session=session)
    try:
        await service.delete_review(review_id=review_id, user_id=current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception:
        logger.exception("Не удалось удалить отзыв")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
