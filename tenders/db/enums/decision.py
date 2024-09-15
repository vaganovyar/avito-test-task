from enum import Enum


class Decision(str, Enum):
    APPROVED = "Approved"
    REJECTED = "Rejected"
