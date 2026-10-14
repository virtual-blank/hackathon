import uuid

from fastapi import APIRouter, HTTPException, Query, status

from src.auth.deps import CurrentUserIdDep, SessionDep
from src.social.schemas import MessageCreateSchema, MessageOutputSchema
from src.social.service import SocialService

router = APIRouter(prefix="/social", tags=["💬 Social"])


# == SEND MESSAGE ==
@router.post(
    "/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageOutputSchema,
    description="Send Message",
)
async def send_message(payload: MessageCreateSchema, user_id: CurrentUserIdDep, session: SessionDep):
    service = SocialService(session=session)
    try:
        return await service.send_message(
            sender_id=user_id,
            receiver_id=payload.receiver_id,
            content=payload.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from e


# == GET HISTORY ==
@router.get(
    "/messages/{peer_id}",
    status_code=status.HTTP_200_OK,
    response_model=list[MessageOutputSchema],
    description="Get Dialog History",
)
async def get_history(
    peer_id: uuid.UUID,
    user_id: CurrentUserIdDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    before_id: uuid.UUID | None = Query(default=None),
):
    service = SocialService(session=session)
    try:
        return await service.get_history(
            user_id=user_id,
            peer_id=peer_id,
            limit=limit,
            before_id=before_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from e
