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
        async with asyncio.TaskGroup() as tg:
            q = asyncio.Queue()

            for provider in self.initialized_providers:
                async def consume(provider=provider, q=q):
                    try:
                        async for x in provider.search(params):
                            if self._filter(x, params):
                                await q.put(x)
                    except Exception:
                        traceback.print_exc()
                    finally:
                        await q.put(None)

                tg.create_task(consume())

            done = 0
            while done < len(self.initialized_providers):
                item = await q.get()
                if item is None:
                    done += 1
                    continue
                yield item

    async def close(self):
        await asyncio.gather(
            *[provider.close() for provider in self.initialized_providers]
        )
        await self.playwright.stop()
