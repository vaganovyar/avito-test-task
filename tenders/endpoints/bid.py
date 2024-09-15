from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status

from tenders.db.connection import get_session
from tenders.db.enums import BidStatus, CreatorType, Decision
from tenders.schemas.bid import Bid, GetBidsResponse, GetFeedbacksResponse, NewBidRequest, PatchBidEditRequest
from tenders.utils.bid import (
    add_bid,
    get_bid_by_id,
    get_tender_bids,
    get_user_bids,
    get_user_tender_feedbacks,
    patch_bid_history,
    put_bid_decision,
    put_bid_status,
    put_feedback,
    rollback_version_bid,
    validate_user_bid,
)
from tenders.utils.employee import get_employee_by_id, get_employee_by_username, validate_employee_organisation
from tenders.utils.organization import get_organization_by_id
from tenders.utils.tender import get_tender_by_id


api_router = APIRouter(
    prefix="/bids",
    tags=["Bids"],
)


@api_router.post(
    "/new",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_post_bid(
    request: NewBidRequest,
    session: AsyncSession = Depends(get_session),
):
    tender = await get_tender_by_id(request.tenderId, session)
    if tender is None:
        return JSONResponse(status_code=http_status.HTTP_404_NOT_FOUND, content={"reason": "tender was not found"})

    if request.authorType == CreatorType.USER:
        user = await get_employee_by_id(request.authorId, session)
        if user is None:
            return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    else:
        organization = await get_organization_by_id(request.authorId, session)
        if organization is None:
            return JSONResponse(
                status_code=http_status.HTTP_403_FORBIDDEN, content={"reason": "organization was not found"}
            )

    return await add_bid(request, session)


@api_router.get(
    "/my",
    response_model=GetBidsResponse,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_my_bids(
    username: str,
    limit: int = 5,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    user = await get_employee_by_username(username, session)
    if username is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})

    return await get_user_bids(user.id, limit, offset, session)


@api_router.get(
    "/{tender_id}/list",
    response_model=GetBidsResponse,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_bids(
    tender_id: UUID4,
    username: str,
    limit: int = 5,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    user = await get_employee_by_username(username, session)
    if user is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})

    return await get_tender_bids(tender_id, user.id, limit, offset, session)


@api_router.get(
    "/{bid_id}/status",
    response_model=BidStatus,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_bid_status(
    bid_id: UUID4,
    username: str,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    bid = await get_bid_by_id(bid_id, session)

    return bid.status


@api_router.put(
    "/{bid_id}/status",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_put_bid_status(
    bid_id: UUID4,
    username: str,
    status: BidStatus,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    await put_bid_status(bid_id, status, session)

    return await get_bid_by_id(bid_id, session)


@api_router.patch(
    "/{bid_id}/edit",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_patch_bid(
    request: PatchBidEditRequest,
    bid_id: UUID4,
    username: str,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    bid = await get_bid_by_id(bid_id, session)

    return await patch_bid_history(bid.id, request.name, request.description, session)


@api_router.put(
    "/{bid_id}/feedback",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_put_feedback(
    bid_id: UUID4,
    username: str,
    bidFeedback: str,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    user = await get_employee_by_username(username, session)
    bid = await get_bid_by_id(bid_id, session)
    await put_feedback(bid_id, user.id, bidFeedback, session)

    return bid


@api_router.get(
    "/{tender_id}/reviews",
    response_model=GetFeedbacksResponse,
    status_code=http_status.HTTP_200_OK,
)
async def router_get_reviews(
    tender_id: UUID4,
    authorUsername: str,
    requesterUsername: str,
    limit: int = 5,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    tender = await get_tender_by_id(tender_id, session)
    if tender is None:
        return JSONResponse(status_code=http_status.HTTP_404_NOT_FOUND, content={"reason": "tender was not found"})
    user = await get_employee_by_username(requesterUsername, session)
    if user is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    user2 = await get_employee_by_username(authorUsername, session)
    if user2 is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})
    validation = await validate_employee_organisation(user.id, tender.organization_id, session)
    if not validation:
        return validation
    author = await get_employee_by_username(authorUsername, session)
    data = await get_user_tender_feedbacks(tender_id, author.id, limit, offset, session)

    return data


@api_router.put(
    "/{bid_id}/rollback/{version}",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_rollback_bid_version(
    bid_id: UUID4,
    version: int,
    username: str,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    await rollback_version_bid(bid_id, version, session)

    return await get_bid_by_id(bid_id, session)


@api_router.put(
    "/{bid_id}/submit_decision",
    response_model=Bid,
    status_code=http_status.HTTP_200_OK,
)
async def router_put_submit_decision(
    bid_id: UUID4,
    decision: Decision,
    username: str,
    session: AsyncSession = Depends(get_session),
):
    validation = await validate_user_bid(username, bid_id, session)
    if validation is not None:
        return validation

    await put_bid_decision(bid_id, decision, session)

    return await get_bid_by_id(bid_id, session)
