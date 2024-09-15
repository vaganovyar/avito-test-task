from datetime import datetime

from pydantic import UUID4
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from tenders.db.enums import ServiceType, TenderStatus
from tenders.db.models import TenderHistory
from tenders.db.models.tender import Tender
from tenders.schemas.tender import NewTenderRequest
from tenders.schemas.tender import Tender as SchemaTender
from tenders.utils.employee import get_employee_by_username, validate_employee_organisation
from tenders.utils.tender_history import add_new_version, rollback_version


async def process_tender(tender: Tender, session: AsyncSession) -> SchemaTender:
    query = select(TenderHistory).where(TenderHistory.tender_id == tender.id)
    history = await session.scalars(query)
    history = max(history, key=lambda x: x.history_number)

    return SchemaTender(
        id=tender.id,
        name=history.name,
        description=history.description,
        status=tender.status,
        serviceType=history.service_type,
        organizationId=tender.organization_id,
        version=history.history_number,
        createdAt=tender.created_at,
    )


async def validate_tender_user(tender_id: UUID4, username: str, session: AsyncSession):
    tender = await get_tender_by_id(tender_id, session)
    if tender is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"reason": "tender was not found"})
    user = await get_employee_by_username(username, session)
    if user is None:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    if not (
        tender.creator_id == user.id or await validate_employee_organisation(user.id, tender.organization_id, session)
    ):
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"reason": "not enough rights"})

    return None


async def get_tenders(limit: int, offset: int, service_type: ServiceType | None, session: AsyncSession) -> list[Tender]:
    query = select(Tender).where(Tender.status == TenderStatus.PUBLISHED.value)
    tenders = await session.scalars(query)
    tenders = [await process_tender(tender, session) for tender in tenders]
    tenders.sort(key=lambda x: x.name)
    return_tenders = []
    if service_type is not None:
        for i in filter(lambda x: x.serviceType == service_type, tenders):
            return_tenders.append(i)
            if len(return_tenders) >= limit + offset:
                break
    else:
        return_tenders = tenders

    return return_tenders[offset : (limit + offset)]


async def add_tender(data: NewTenderRequest, creator_id: UUID4, session: AsyncSession):
    tender = Tender(
        organization_id=data.organizationId,
        status=TenderStatus("Created"),
        creator_id=creator_id,
    )
    session.add(tender)
    await session.flush()
    await session.refresh(tender)

    tender_history = TenderHistory(
        tender_id=tender.id,
        name=data.name,
        description=data.description,
        service_type=data.serviceType,
        history_number=1,
    )
    session.add(tender_history)
    await session.flush()
    await session.refresh(tender_history)

    await session.commit()

    return {
        "id": tender.id,
        "name": data.name,
        "description": data.description,
        "status": tender.status,
        "organizationId": data.organizationId,
        "serviceType": data.serviceType,
        "version": tender_history.history_number,
        "createdAt": tender.created_at,
    }


async def get_tenders_by_user(user_id: UUID4, limit: int, offset: int, session: AsyncSession) -> list[Tender]:
    query = select(Tender).where(Tender.creator_id == user_id)
    tenders = await session.scalars(query)
    tenders = [await process_tender(tender, session) for tender in tenders]
    tenders.sort(key=lambda x: x.name)

    return tenders[offset : (offset + limit)]


async def get_tender_by_id(tender_id: UUID4, session: AsyncSession) -> SchemaTender:
    query = select(Tender).where(Tender.id == tender_id)
    tender = await session.scalar(query)

    return tender


async def put_tender_status(tender_id: UUID4, tender_status: TenderStatus, session: AsyncSession):
    query = update(Tender).where(Tender.id == tender_id).values(updated_at=datetime.now(), status=tender_status)
    await session.execute(query)
    await session.commit()


async def patch_tender_history(
    tender_id: UUID4, name: str, description: str, service_type: ServiceType, session: AsyncSession
):
    tender = await get_tender_by_id(tender_id, session)
    tender = await process_tender(tender, session)
    await add_new_version(tender, name, description, service_type, session)
    tender.version += 1
    if name is not None:
        tender.name = name
    if description is not None:
        tender.description = description
    if service_type is not None:
        tender.serviceType = service_type

    return tender


async def rollback_version_tender(tender_id: UUID4, version: int, session: AsyncSession):
    tender = await get_tender_by_id(tender_id, session)
    tender = await process_tender(tender, session)
    await rollback_version(tender, version, session)
    tender = await get_tender_by_id(tender_id, session)

    return await process_tender(tender, session)
