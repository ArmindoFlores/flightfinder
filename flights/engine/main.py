import asyncio
import typing
import traceback

from playwright.async_api import Playwright, async_playwright
from requests_async import AsyncSession

from flights.providers import BaseProvider, providers
from flights.search import SearchParams, SearchResults


class FlightFinder:
    def __init__(self, providers: typing.Optional[typing.List[typing.Type[BaseProvider]]] = None):
        self.providers = providers
        self.initialized_providers: typing.List[BaseProvider] = []
        self.requests: typing.Optional[AsyncSession] = None
        self.playwright: typing.Optional[Playwright] = None

    def _filter(self, result: SearchResults, params: SearchParams) -> bool:
        if result["datetime"].date() > params["end_date"]:
            return False
        if result["datetime"].date() < params["start_date"]:
            return False
        return True

    async def init(self):
        self.requests = AsyncSession()
        self.playwright = await async_playwright().start()
        providers_ = providers if self.providers is None else self.providers
        self.initialized_providers = [provider() for provider in providers_]
        await asyncio.gather(
            *[provider.init(self.playwright, self.requests) for provider in self.initialized_providers]
        )

    async def search(self, params: SearchParams) -> typing.AsyncGenerator[SearchResults, None]:
        coros = [provider.search(params) for provider in self.initialized_providers]
        for fut in asyncio.as_completed(coros):
            try:
                items = await fut
                if items is None:
                    continue
                for x in items:
                    if self._filter(x, params):
                        yield x
            except Exception:
                traceback.print_exc()

    async def close(self):
        await asyncio.gather(
            *[provider.close() for provider in self.initialized_providers]
        )
        await self.playwright.stop()
