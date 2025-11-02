import typing

from playwright.async_api import Playwright
from requests_async import AsyncSession

from flights import search


class BaseProvider:
    async def init(self, playwright: Playwright, requests: AsyncSession) -> None:
        raise NotImplementedError

    async def search(self, params: search.SearchParams) -> typing.AsyncGenerator[search.SearchResults, None]:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError
