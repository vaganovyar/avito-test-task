from datetime import datetime

from pydantic import UUID4
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status as http_status
from starlette.responses import JSONResponse

from tenders.db.enums import BidStatus, CreatorType, Decision, TenderStatus
from tenders.db.models import Bid, BidHistory, Feedback, FeedbackHistory, OrganizationResponsible, Tender
from tenders.schemas.bid import Bid as SchemaBid
from tenders.schemas.bid import Feedback as SchemaFeedback
from tenders.schemas.bid import NewBidRequest
from tenders.utils.bid_history import add_new_version, rollback_version
from tenders.utils.employee import get_employee_by_username, validate_employee_organisation
from tenders.utils.organization import get_quorum
from tenders.utils.tender import get_tender_by_id


async def process_bid(bid: Bid, session: AsyncSession):
    query = select(BidHistory).where(BidHistory.bid_id == bid.id)
    history = await session.scalars(query)
    history = max(history, key=lambda x: x.history_number)

    return SchemaBid(
        id=bid.id,
        name=history.name,
        description=history.description,
        status=bid.status,
        tenderId=bid.tender_id,
        authorType=bid.creator_type,
        authorId=bid.creator_id,
        version=history.history_number,
        createdAt=bid.created_at,
    )


async def process_feedback(feedback: Feedback, session: AsyncSession):
    query = select(FeedbackHistory).where(FeedbackHistory.feedback_id == feedback.id)
    history = await session.scalars(query)
    history = max(history, key=lambda x: x.history_number)

    return SchemaFeedback(
        id=feedback.id,
        description=history.description,
        createdAt=feedback.created_at,
    )


async def validate_user_bid(username: str, bid_id: UUID4, session: AsyncSession):
    user = await get_employee_by_username(username, session)
    if username is None:
        return JSONResponse(status_code=http_status.HTTP_401_UNAUTHORIZED, content={"reason": "user was not found"})

    bid = await get_bid_by_id(bid_id, session)
    if bid is None:
        return JSONResponse(status_code=http_status.HTTP_404_NOT_FOUND, content={"reason": "bid was not found"})

    if not (
        (bid.authorType == CreatorType.USER and bid.authorId == user.id)
        or (
            bid.authorType == CreatorType.ORGANIZATION
            and await validate_employee_organisation(user.id, bid.authorId, session)
        )
    ):
        query = select(Tender).where(Tender.id == bid.tenderId)
        tender = await session.scalar(query)
        if not await validate_employee_organisation(user.id, tender.organization_id, session):
            return JSONResponse(status_code=http_status.HTTP_403_FORBIDDEN, content={"reason": "not enough rights"})

    return None


async def add_bid(data: NewBidRequest, session: AsyncSession):
    bid = Bid(
        tender_id=data.tenderId,
        status=BidStatus.CREATED,
        creator_type=data.authorType,
        creator_id=data.authorId,
    )
    session.add(bid)
    await session.flush()
    await session.refresh(bid)

    bid_history = BidHistory(
        bid_id=bid.id,
        name=data.name,
        description=data.description,
        history_number=1,
    )
    session.add(bid_history)
    await session.flush()
    await session.refresh(bid_history)

    await session.commit()

    return {
        "id": bid.id,
        "name": data.name,
        "description": data.description,
        "status": bid.status,
        "tenderId": data.tenderId,
        "authorType": data.authorType,
        "authorId": data.authorId,
        "version": bid_history.history_number,
        "createdAt": bid.created_at,
    }


async def get_user_bids(user_id: UUID4, limit: int, offset: int, session: AsyncSession):
    query = select(Bid).where(Bid.creator_id == user_id, Bid.creator_type == CreatorType.USER)
    bids = await session.scalars(query)
    bids = [await process_bid(bid, session) for bid in bids]

    query = select(OrganizationResponsible).where(OrganizationResponsible.user_id == user_id)
    organizations = await session.scalars(query)
    for organization in organizations:
        query = select(Bid).where(
            Bid.creator_id == organization.organization_id, Bid.creator_type == CreatorType.ORGANIZATION
        )
        current_bids = await session.scalars(query)
        current_bids = [await process_bid(bid, session) for bid in current_bids]
        bids += current_bids

        query = select(Tender).where(Tender.organization_id == organization.organization_id)
        tenders = await session.scalars(query)
        for tender in tenders:
            query = select(Bid).where(Bid.tender_id == tender.id)
            current_bids = await session.scalars(query)
            current_bids = [await process_bid(bid, session) for bid in current_bids]
            bids += current_bids

    bids = list(set(bids))
    bids.sort(key=lambda x: x.name)

    return bids[offset : (offset + limit)]


async def get_tender_bids(tender_id: UUID4, user_id: UUID4, limit: int, offset: int, session: AsyncSession):
    query = select(Bid).where(Bid.tender_id == tender_id)
    bids = await session.scalars(query)
    bids = [await process_bid(bid, session) for bid in bids]
    new_bids = []
    for bid in bids:
        if (
            bid.status == BidStatus.PUBLISHED
            or (bid.authorType == CreatorType.USER and bid.authorId == user_id)
            or (
                bid.authorType == CreatorType.ORGANIZATION
                and await validate_employee_organisation(user_id, bid.authorId, session)
            )
        ):
            new_bids.append(bid)
        else:
            query = select(Tender).where(Tender.id == bid.tenderId)
            tender = await session.scalar(query)
            if await validate_employee_organisation(user_id, tender.organization_id, session):
                new_bids.append(bid)
    bids = new_bids
    bids.sort(key=lambda x: x.name)

    return bids[offset : (offset + limit)]


async def get_bid_by_id(bid_id: UUID4, session: AsyncSession):
    query = select(Bid).where(Bid.id == bid_id)
    bid = await session.scalar(query)

    return await process_bid(bid, session)


async def put_bid_status(bid_id: UUID4, status: BidStatus, session: AsyncSession):
    query = update(Bid).where(Bid.id == bid_id).values(updated_at=datetime.now(), status=status)
    await session.execute(query)
    await session.commit()


async def patch_bid_history(
    bid_id: UUID4,
    name: str,
    description: str,
    session: AsyncSession,
):
    bid = await get_bid_by_id(bid_id, session)
    await add_new_version(bid, name, description, session)
    bid.version += 1
    if name is not None:
        bid.name = name
    if description is not None:
        bid.description = description

    return bid


async def put_feedback(
    bid_id: UUID4,
    user_id: UUID4,
    description: str,
    session: AsyncSession,
):
    feedback = Feedback(
        bid_id=bid_id,
        creator_id=user_id,
    )
    session.add(feedback)
    await session.flush()
    await session.refresh(feedback)

    history = FeedbackHistory(
        feedback_id=feedback.id,
        description=description,
        history_number=1,
    )
    session.add(history)
    await session.flush()
    await session.refresh(history)

    await session.commit()


async def rollback_version_bid(
    bid_id: UUID4,
    version: int,
    session: AsyncSession,
):
    bid = await get_bid_by_id(bid_id, session)
    await rollback_version(bid, version, session)
    bid = await get_bid_by_id(bid_id, session)

    return bid


async def get_user_bid_feedbacks(bid_id: UUID4, user_id: UUID4, session: AsyncSession):
    query = select(Feedback).where(Feedback.bid_id == bid_id, Feedback.creator_id == user_id)
    feedbacks = await session.scalars(query)
    return [await process_feedback(feedback, session) for feedback in feedbacks]


async def get_user_tender_feedbacks(tender_id: UUID4, user_id: UUID4, limit: int, offset: int, session: AsyncSession):
    query = select(Bid).where(Bid.tender_id == tender_id)
    bids = await session.scalars(query)
    feedbacks = []
    for bid in bids:
        feedbacks += await get_user_bid_feedbacks(bid.id, user_id, session)
    feedbacks.sort(key=lambda x: x.description)

    return feedbacks[offset : (offset + limit)]


async def put_bid_decision(bid_id: UUID4, decision: Decision, session: AsyncSession):
    if decision == Decision.REJECTED:
        query = update(Bid).where(Bid.id == bid_id).values(status=BidStatus.CANCELED)
        await session.execute(query)
        await session.commit()
    else:
        bid_query = select(Bid).where(Bid.id == bid_id)
        bid = await session.scalar(bid_query)
        tender = await get_tender_by_id(bid.tender_id, session)
        quorum = await get_quorum(tender.organization_id, session)
        if bid.approved_num + 1 >= min(3, quorum):
            query = update(Bid).where(Bid.id == bid_id).values(status=BidStatus.CANCELED)
            await session.execute(query)
            query = update(Tender).where(Tender.id == tender.id).values(status=TenderStatus.CLOSED)
            await session.execute(query)
            await session.commit()
        else:
            query = update(Bid).where(Bid.id == bid_id).values(approved_num=bid.approved_num + 1)
            await session.execute(query)
            await session.commit()
