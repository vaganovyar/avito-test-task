from sqlalchemy import Column
from sqlalchemy import Enum as SqlalchemyEnum
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import INTEGER, TEXT, TIMESTAMP, UUID, VARCHAR

from tenders.db import DeclarativeBase
from tenders.db.enums import ServiceType


class TenderHistory(DeclarativeBase):
    __tablename__ = "tender_history"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    tender_id = Column("tender_id", UUID(as_uuid=True), ForeignKey("tender.id"))
    name = Column("name", VARCHAR(100))
    description = Column("description", TEXT)
    service_type = Column("service_type", SqlalchemyEnum(ServiceType))
    history_number = Column("history_number", INTEGER)
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
