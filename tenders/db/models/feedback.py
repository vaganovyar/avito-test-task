from sqlalchemy import Column
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

from tenders.db import DeclarativeBase


class Feedback(DeclarativeBase):
    __tablename__ = "feedback"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    bid_id = Column("bid_id", UUID(as_uuid=True), ForeignKey("bid.id"))
    creator_id = Column("creator_id", UUID(as_uuid=True), ForeignKey("employee.id"))
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
