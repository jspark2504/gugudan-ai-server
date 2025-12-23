from enum import Enum

class ChatRoomStatus(Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    ENDED = "ENDED"

class ChatCategory(Enum):
    LOVE = "LOVE"
    BREAKUP = "BREAKUP"
    DIVORCE = "DIVORCE"
    ETC = "ETC"

class ChatDivision(Enum):
    CONSULT = "CONSULT"
    ANALYSIS = "ANALYSIS"
    FREE = "FREE"

class SatisfiedStatus(Enum):
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"