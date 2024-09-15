from sqlalchemy import Column
from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import INTEGER, TEXT, TIMESTAMP, UUID

from tenders.db import DeclarativeBase


class FeedbackHistory(DeclarativeBase):
    __tablename__ = "feedback_history"

    id = Column("id", UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    feedback_id = Column("feedback_id", UUID(as_uuid=True), ForeignKey("feedback.id"))
    description = Column("description", TEXT)
    history_number = Column("history_number", INTEGER)
    created_at = Column("created_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column("updated_at", TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        columns = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        return f'<{self.__tablename__}: {", ".join(map(lambda x: f"{x[0]}={x[1]}", columns.items()))}>'
