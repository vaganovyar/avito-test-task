from sqlalchemy import Column
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from tenders.db import DeclarativeBase


class OrganizationResponsible(DeclarativeBase):
    __tablename__ = "organization_responsible"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    organization_id = Column("organization_id", UUID(as_uuid=True), ForeignKey("organization.id"))
    user_id = Column("user_id", UUID(as_uuid=True), ForeignKey("employee.id"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
