from sqlalchemy import Column
from sqlalchemy import Enum as SqlalchemyEnum
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import TEXT, TIMESTAMP, UUID, VARCHAR

from tenders.db import DeclarativeBase
from tenders.db.enums import OrganizationType


class Organization(DeclarativeBase):
    __tablename__ = "organization"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    name = Column("name", VARCHAR(100), nullable=False)
    description = Column("description", TEXT)
    type = Column("type", SqlalchemyEnum(OrganizationType))
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
