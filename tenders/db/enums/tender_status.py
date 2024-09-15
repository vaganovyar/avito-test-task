from enum import Enum


class TenderStatus(str, Enum):
    CREATED = "Created"
    PUBLISHED = "Published"
    CLOSED = "Closed"
