from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tenders.db.models import BidHistory
from tenders.schemas.bid import Bid as SchemaBid


async def add_new_version(
    bid: SchemaBid,
    name: str,
    description: str,
    session: AsyncSession,
):
    if name is None:
        name = bid.name
    if description is None:
        description = bid.description
    bid_history = BidHistory(
        bid_id=bid.id,
        name=name,
        description=description,
        history_number=bid.version + 1,
    )
    session.add(bid_history)
    await session.commit()


async def rollback_version(
    bid: SchemaBid,
    version: int,
    session: AsyncSession,
):
    query = select(BidHistory).where(BidHistory.bid_id == bid.id, BidHistory.history_number == version)
    bid_history = await session.scalar(query)
    await add_new_version(bid, bid_history.name, bid_history.description, session)
