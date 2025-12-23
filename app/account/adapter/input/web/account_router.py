from fastapi import APIRouter, Depends, HTTPException

from app.auth.adapter.input.web.dependencies import (
    get_optional_jwt_payload,
    get_optional_session,
)
from app.auth.application.port.jwt_token_port import TokenPayload
from app.auth.domain.entity.session import Session
from app.config.database.session import get_db_session

from app.account.adapter.input.web.response.update_mbti_gender_response import UpdateMbtiGenderResponse
from app.account.adapter.input.web.request.update_mbti_gender_Request import UpdateMbtiGenderRequest

from app.account.adapter.input.web.response.update_mbti_gender_response import (
    UpdateMbtiGenderResponse,
)
from app.account.application.usecase.account_usecase import AccountUseCase
from app.account.infrastructure.repository.account_repository_impl import AccountRepositoryImpl


# =============================
# DI 객체 (conversation_router 스타일)
# =============================
account_repo = AccountRepositoryImpl()
account_usecase = AccountUseCase(account_repo)

router = APIRouter(prefix="/account", tags=["account"])


# =============================
# 인증 관련
# =============================
def get_current_account_id(
    jwt_payload: TokenPayload | None = Depends(get_optional_jwt_payload),
    session: Session | None = Depends(get_optional_session),
) -> int:

    if jwt_payload:
        return jwt_payload.account_id
    if session:
        return session.account_id
    raise HTTPException(status_code=401, detail="Not authenticated")


# =============================
# PATCH 내 MBTI / Gender 수정
# =============================
@router.patch("/my/profile/mbti-gender/edit", response_model=UpdateMbtiGenderResponse)
def edit_my_mbti_gender(
    req: UpdateMbtiGenderRequest,
    account_id: int = Depends(get_current_account_id),
    db: Session = Depends(get_db_session),
):
    if req.gender is None and req.mbti is None:
        raise HTTPException(status_code=400, detail="Nothing to update")

    repo = AccountRepositoryImpl(db)
    usecase = AccountUseCase(repo)

    updated = usecase.update_my_mbti_gender(
        account_id=account_id,
        gender=req.gender,
        mbti=req.mbti,
    )

    return UpdateMbtiGenderResponse(
        account_id=updated.id,
        gender=updated.gender,
        mbti=updated.mbti,
    )

