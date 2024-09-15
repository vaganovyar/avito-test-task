from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenders.db.enums import ServiceType
from tenders.db.models.tender_history import TenderHistory
from tenders.schemas.tender import Tender as SchemaTender


async def add_new_version(
    tender: SchemaTender, name: str, description: str, service_type: ServiceType, session: AsyncSession
):
    if name is None:
        name = tender.name
    if description is None:
        description = tender.description
    if service_type is None:
        service_type = tender.serviceType
    tender_history = TenderHistory(
        tender_id=tender.id,
        name=name,
        description=description,
        service_type=service_type,
        history_number=tender.version + 1,
    )
    session.add(tender_history)
    await session.commit()


async def rollback_version(tender: SchemaTender, version: int, session: AsyncSession):
    query = select(TenderHistory).where(TenderHistory.tender_id == tender.id, TenderHistory.history_number == version)
    tender_history = await session.scalar(query)
    await add_new_version(tender, tender_history.name, tender_history.description, tender_history.service_type, session)
