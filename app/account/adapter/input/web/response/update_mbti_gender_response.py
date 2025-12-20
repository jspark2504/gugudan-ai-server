from typing import Optional
from pydantic import BaseModel

from app.account.domain.entity.account_enums import Gender, Mbti


class UpdateMbtiGenderResponse(BaseModel):
    account_id: int
    gender: Optional[Gender] = None
    mbti: Optional[Mbti] = None
