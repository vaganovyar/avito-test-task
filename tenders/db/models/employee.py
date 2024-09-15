from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID, VARCHAR

from tenders.db import DeclarativeBase


class Employee(DeclarativeBase):
    __tablename__ = "employee"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    username = Column("username", VARCHAR(50), unique=True, nullable=False)
    first_name = Column("first_name", VARCHAR(50))
    last_name = Column("last_name", VARCHAR(50))
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
