from datetime import datetime
from typing import TypedDict, Optional

class CounselRow(TypedDict):
    id: int
    role: str
    message: str
    parent: Optional[int]
    iv: str
    created_at: datetime