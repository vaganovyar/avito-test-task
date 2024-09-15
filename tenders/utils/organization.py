from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenders.db.models import Organization, OrganizationResponsible


async def get_organization_by_id(organization_id: UUID4, session: AsyncSession):
    query = select(Organization).where(Organization.id == organization_id)
    organization = await session.scalar(query)

    return organization


async def get_quorum(organization_id: UUID4, session: AsyncSession):
    query = select(OrganizationResponsible).where(OrganizationResponsible.organization_id == organization_id)
    rows = await session.scalars(query)

    return len(rows.all())
