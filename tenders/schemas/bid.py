from datetime import datetime

from pydantic import BaseModel, RootModel
from pydantic.types import UUID4

from tenders.db.enums import BidStatus, CreatorType


class NewBidRequest(BaseModel):
    name: str
    description: str
    tenderId: UUID4
    authorType: CreatorType
    authorId: UUID4


class Bid(BaseModel):
    id: UUID4
    name: str
    description: str
    status: BidStatus
    tenderId: UUID4
    authorType: CreatorType
    authorId: UUID4
    version: int
    createdAt: datetime

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)


class GetBidsResponse(RootModel):
    root: list[Bid]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class PatchBidEditRequest(BaseModel):
    name: str = None
    description: str = None


class Feedback(BaseModel):
    id: UUID4
    description: str
    createdAt: datetime


class GetFeedbacksResponse(RootModel):
    root: list[Feedback]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
