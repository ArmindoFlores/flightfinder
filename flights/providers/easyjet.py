__all__ = [
    "EasyJet",
]

import datetime

from playwright.async_api import Playwright, TimeoutError
from requests_async import AsyncSession

from flights import search
from .base import BaseProvider


class EasyJetSearchParams(search.SearchParams, total=False):
    pass


class EasyJet(BaseProvider):
    BASE_URL = "https://www.easyjet.com"
    AVAILABILITY_ENDPOINT = "homepage/api/availability"
    SCRIPT = """
    async (url) => {
        try {
            const res = await fetch(url, {
                method: "GET",
                credentials: "include",
            });
            const json = await res.json();
            return { ok: res.ok, status: res.status, json };
        } catch (e) {
            return { ok: false, status: 0, error: String(e) };
        }
    }
    """
    
    async def init(self, playwright: Playwright, requests: AsyncSession):
        self.chromium = playwright.chromium

        self.browser = await self.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    def _get_search_query_params(self, params: EasyJetSearchParams):
        return "&".join(
            f"{key!s}={value!s}"
            for key, value in params.items()
        )
    
    def _format_results(self, results) -> search.SearchResults:
        return [
            {
                "price": result["price"],
                "datetime": datetime.datetime.fromisoformat(result["date"]),
                "provider": "easyjet",
            } for result in results["departureFlights"]
        ]

    async def search(self, params: EasyJetSearchParams):
        await self.page.goto(self.BASE_URL, wait_until="domcontentloaded")        
        await self.page.wait_for_load_state("domcontentloaded")

        try:
            await self.page.locator("#ensCloseBanner").click()
            await self.page.wait_for_load_state("domcontentloaded")
        except TimeoutError:
            pass

        query_string = self._get_search_query_params(params)
        result = await self.page.evaluate(
            self.SCRIPT, 
            f"{self.BASE_URL}/{self.AVAILABILITY_ENDPOINT}?{query_string}"
        )
        
        if result["ok"] and result["json"]:
            return self._format_results(result["json"])
        return None
    
    async def close(self):
        await self.browser.close()
