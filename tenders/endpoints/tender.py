from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status

from tenders.db.connection import get_session
from tenders.db.enums import ServiceType, TenderStatus
from tenders.schemas.tender import GetTendersResponse, NewTenderRequest, PatchTenderEditRequest, Tender
from tenders.utils.employee import get_employee_by_username, validate_employee_organisation
from tenders.utils.tender import (
    add_tender,
    get_tender_by_id,
    get_tenders,
    get_tenders_by_user,
    patch_tender_history,
    process_tender,
    put_tender_status,
    rollback_version_tender,
    validate_tender_user,
)


api_router = APIRouter(
    prefix="/tenders",
    tags=["Tenders"],
)


@api_router.get(
    "",
    response_model=GetTendersResponse,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_tenders(
    limit: int = 5, offset: int = 0, service_type: ServiceType = None, session: AsyncSession = Depends(get_session)
):
    if limit < 0:
        return JSONResponse(status_code=http_status.HTTP_400_BAD_REQUEST, content={"reason": "invalid limit"})
    if offset < 0:
        return JSONResponse(status_code=http_status.HTTP_400_BAD_REQUEST, content={"reason": "invalid offset"})

    return await get_tenders(limit, offset, service_type, session)


@api_router.post(
    "/new",
    response_model=Tender,
    status_code=http_status.HTTP_200_OK,
)
async def router_post_tender(
    tender_request: NewTenderRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await get_employee_by_username(tender_request.creatorUsername, session)
    if user is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    if not await validate_employee_organisation(user.id, tender_request.organizationId, session):
        return JSONResponse(
            status_code=http_status.HTTP_403_FORBIDDEN, content={"reason": "user not authorized for this organization"}
        )

    return await add_tender(tender_request, user.id, session)


@api_router.get(
    "/my",
    response_model=GetTendersResponse,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_my_tenders(
    username: str, limit: int = 5, offset: int = 0, session: AsyncSession = Depends(get_session)
):
    if limit < 0:
        return JSONResponse(status_code=http_status.HTTP_400_BAD_REQUEST, content={"reason": "invalid limit"})
    if offset < 0:
        return JSONResponse(status_code=http_status.HTTP_400_BAD_REQUEST, content={"reason": "invalid offset"})
    user = await get_employee_by_username(username, session)
    if user is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})

    return await get_tenders_by_user(user.id, limit, offset, session)


@api_router.get(
    "/{tender_id}/status",
    response_model=TenderStatus,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_tender_status(
    tender_id: UUID4, username: str = None, session: AsyncSession = Depends(get_session)
):
    tender = await get_tender_by_id(tender_id, session)
    if tender is None:
        return JSONResponse(status_code=http_status.HTTP_404_NOT_FOUND, content={"reason": "tender was not found"})
    if tender.status == TenderStatus.PUBLISHED:
        return tender.status

    user = await get_employee_by_username(username, session)
    if user is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    if tender.creator_id == user.id or await validate_employee_organisation(user.id, tender.organization_id, session):
        return tender.status

    return JSONResponse(status_code=http_status.HTTP_403_FORBIDDEN, content={"reason": "not enough rights"})


@api_router.put(
    "/{tender_id}/status",
    response_model=Tender,
    status_code=http_status.HTTP_200_OK,
)
async def router_put_tender_status(
    tender_id: UUID4, username: str, status: TenderStatus, session: AsyncSession = Depends(get_session)
):
    validation = await validate_tender_user(tender_id, username, session)
    if validation is not None:
        return validation
    await put_tender_status(tender_id, status, session)
    tender = await get_tender_by_id(tender_id, session)

    print(await process_tender(tender, session))
    return await process_tender(tender, session)


@api_router.patch(
    "/{tender_id}/edit",
    response_model=Tender,
    status_code=http_status.HTTP_200_OK,
)
async def router_patch_tender(
    tender_id: UUID4, username: str, edit_request: PatchTenderEditRequest, session: AsyncSession = Depends(get_session)
):
    validation = await validate_tender_user(tender_id, username, session)
    if validation is not None:
        return validation

    return await patch_tender_history(
        tender_id, edit_request.name, edit_request.description, edit_request.serviceType, session
    )


@api_router.put(
    "/{tender_id}/rollback/{version}",
    response_model=Tender,
    status_code=http_status.HTTP_200_OK,
)
async def router_rollback_tender_version(
    tender_id: UUID4, username: str, version: int, session: AsyncSession = Depends(get_session)
):
    validation = await validate_tender_user(tender_id, username, session)
    if validation is not None:
        return validation

    return await rollback_version_tender(tender_id, version, session)
