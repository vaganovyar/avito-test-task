from enum import Enum


class BidStatus(str, Enum):
    CREATED = "Created"
    PUBLISHED = "Published"
    CANCELED = "Canceled"
