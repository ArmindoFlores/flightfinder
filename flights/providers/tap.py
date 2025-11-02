__all__ = [
    "TAP",
]

import datetime
from contextlib import AsyncExitStack

from playwright.async_api import Playwright
from requests_async import AsyncSession

from flights import search
from .base import BaseProvider


class TAPSearchParams(search.SearchParams, total=False):
    pass

class TAP(BaseProvider):
    BASE_URL = "https://www.flytap.com"
    AVAILABILITY_ENDPOINT = "api/calendar"

    def _market_from_currency(self, currency: str):
        return "PT"

    def _get_search_params(self, params: TAPSearchParams):
        return {
            "market": self._market_from_currency(params["currency"]),
            "origin": params["origin"],
            "destination": params["destination"],
            "tripType": "R" if params["return_journey"] else "O",
            "year": str(params["start_date"].year),
            "month": str(params["start_date"].month),
            "payWithMiles": False,
            "starAlliance": False,
            "paxType": "ADT",
            "cabinClass": "E",
        }
    
    def _format_results(self, results) -> search.SearchResults:
        return [
            {
                "price": result["bestTotalPrice"],
                "datetime": datetime.datetime.fromisoformat(result["departureDate"]),
                "provider": "tap",
            } for result in results["data"]["bestPriceForDates"] if not result["soldOut"]
        ]
    
    async def init(self, playwright: Playwright, requests: AsyncSession):
        self.cm = requests
        self.stack = AsyncExitStack()
        self.requests = await self.stack.enter_async_context(self.cm)

    async def search(self, params: TAPSearchParams):
        search_params = self._get_search_params(params)
        result = await self.requests.post(
            f"{self.BASE_URL}/{self.AVAILABILITY_ENDPOINT}?functionName=calendar",
            json=search_params
        )
        
        if result.status_code == 200:
            return self._format_results(result.json())
        return None
    
    async def close(self):
        await self.stack.aclose()
