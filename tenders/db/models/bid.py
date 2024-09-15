from sqlalchemy import Column
from sqlalchemy import Enum as SqlalchemyEnum
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID

from tenders.db import DeclarativeBase
from tenders.db.enums import BidStatus
from tenders.db.enums.creator_type import CreatorType


class Bid(DeclarativeBase):
    __tablename__ = "bid"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    tender_id = Column("tender_id", UUID(as_uuid=True), ForeignKey("tender.id"))
    status = Column("status", SqlalchemyEnum(BidStatus))
    creator_type = Column("creator_type", SqlalchemyEnum(CreatorType))
    creator_id = Column("creator_id", UUID(as_uuid=True))
    approved_num = Column("approved_num", INTEGER, server_default=text("0"))
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)
