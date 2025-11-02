__all__ = [
    "TAP",
]

import datetime
import typing
from contextlib import AsyncExitStack

from playwright.async_api import Playwright
from requests_async import AsyncSession

from flights import search, utils
from .base import BaseProvider


class TAPSearchParams(search.SearchParams, total=False):
    pass

class TAP(BaseProvider):
    BASE_URL = "https://www.flytap.com"
    AVAILABILITY_ENDPOINT = "api/calendar"

    @staticmethod
    def _month_range(start: datetime.date, end: datetime.date):
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            yield (year, month)
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1

    @staticmethod
    def _market_from_currency(currency: str):
        return "PT"

    @staticmethod
    def _get_search_params(params: TAPSearchParams):
        return [{
            "market": TAP._market_from_currency(params["currency"]),
            "origin": params["origin"],
            "destination": params["destination"],
            "tripType": "R" if params["return_journey"] else "O",
            "year": year,
            "month": month,
            "payWithMiles": False,
            "starAlliance": False,
            "paxType": "ADT",
            "cabinClass": "E",
        } for year, month in TAP._month_range(params["start_date"], params["end_date"])]
    
    @staticmethod
    def _format_results(results) -> typing.List[search.SearchResults]:
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

    async def _search(self, json):
        result = await self.requests.post(
            f"{self.BASE_URL}/{self.AVAILABILITY_ENDPOINT}?functionName=calendar",
            json=json
        )
        
        if result.status_code == 200:
            return self._format_results(result.json())
        
        return None

    async def search(self, params: TAPSearchParams):
        async for results in utils.as_completed_limited(
            5,
            (self._search(search_params) for search_params in self._get_search_params(params))
        ):
            for result in results:
                yield result
    
    async def close(self):
        await self.stack.aclose()
