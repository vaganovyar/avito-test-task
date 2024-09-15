from datetime import datetime

from pydantic import BaseModel, RootModel
from pydantic.types import UUID4

from tenders.db.enums import ServiceType, TenderStatus


class Tender(BaseModel):
    id: UUID4
    name: str
    description: str
    status: TenderStatus
    serviceType: ServiceType
    organizationId: UUID4
    version: int
    createdAt: datetime


class NewTenderRequest(BaseModel):
    name: str
    description: str
    serviceType: ServiceType
    organizationId: UUID4
    creatorUsername: str


class GetTendersResponse(RootModel):
    root: list[Tender]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class PatchTenderEditRequest(BaseModel):
    name: str = None
    description: str = None
    serviceType: ServiceType = None
