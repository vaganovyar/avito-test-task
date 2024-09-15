from tenders.endpoints.bid import api_router as bid_router
from tenders.endpoints.ping import api_router as application_health_router
from tenders.endpoints.tender import api_router as tender_router


list_of_routes = [
    application_health_router,
    tender_router,
    bid_router,
]


__all__ = [
    "list_of_routes",
]
