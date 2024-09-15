from sqlalchemy import Column
from sqlalchemy import Enum as SqlalchemyEnum
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

from tenders.db import DeclarativeBase
from tenders.db.enums import TenderStatus


class Tender(DeclarativeBase):
    __tablename__ = "tender"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    organization_id = Column("organization_id", UUID(as_uuid=True), ForeignKey("organization.id"))
    status = Column("status", SqlalchemyEnum(TenderStatus))
    creator_id = Column("creator_id", UUID(as_uuid=True), ForeignKey("employee.id"))
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
