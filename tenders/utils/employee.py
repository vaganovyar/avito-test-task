from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenders.db.models import Employee, OrganizationResponsible


async def validate_employee_organisation(user_id: UUID4, organization_id: UUID4, session: AsyncSession) -> bool:
    query = select(OrganizationResponsible).where(
        OrganizationResponsible.organization_id == organization_id, OrganizationResponsible.user_id == user_id
    )
    result = await session.scalar(query)

    return result is not None


async def get_employee_by_username(username: str, session: AsyncSession) -> Employee | None:
    if username is None:
        return None

    query = select(Employee).where(Employee.username == username)
    user = await session.scalar(query)

    return user


async def get_employee_by_id(user_id: UUID4, session: AsyncSession) -> Employee | None:
    if user_id is None:
        return None

    query = select(Employee).where(Employee.id == user_id)
    user = await session.scalar(query)

    return user
