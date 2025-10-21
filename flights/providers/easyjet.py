__all__ = [
    "EasyJet",
]

from flights import search

from playwright.sync_api import Playwright, TimeoutError


class EasyJetSearchParams(search.SearchParams, total=False):
    pass


class EasyJet:
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
    
    def __init__(self, playwright: Playwright):
        self.chromium = playwright.chromium

        self.browser = self.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        #origin=OPO&destination=GVA&currency=GBP&isReturn=true&startDate=2025-10-18&endDate=2026-10-18&isWorldwide=false

    def _get_search_query_params(self, params: EasyJetSearchParams):
        return "&".join(
            f"{key!s}={value!s}"
            for key, value in params.items()
        )

    def search(self, params: EasyJetSearchParams):
        self.page.goto(self.BASE_URL, wait_until="domcontentloaded")
        
        self.page.wait_for_load_state("networkidle")

        try:
            self.page.locator("#ensCloseBanner").click()
            self.page.wait_for_load_state("networkidle")
        except TimeoutError:
            pass

        query_string = self._get_search_query_params(params)
        result = self.page.evaluate(
            self.SCRIPT, 
            f"{self.BASE_URL}/{self.AVAILABILITY_ENDPOINT}?{query_string}"
        )
        
        if result["ok"] and result["json"]:
            return result["json"]
        return None
    
    def close(self):
        self.browser.close()
