from playwright.sync_api import Page

from config.settings import DEFAULT_TIMEOUT_MS


class BasePage:
    """
    Holds behaviour that every page object needs. There's only one real
    page in this app (the chat screen), but this stays separate so the
    "how do I wait for something" concerns don't get mixed into
    "what does the chat page do".
    """

    def __init__(self, page: Page):
        self.page = page

    def wait_for_visible(self, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS):
        locator = self.page.locator(selector)
        locator.first.wait_for(state="visible", timeout=timeout_ms)
        return locator

    def wait_for_hidden(self, selector: str, timeout_ms: int = DEFAULT_TIMEOUT_MS):
        locator = self.page.locator(selector)
        locator.first.wait_for(state="hidden", timeout=timeout_ms)
        return locator
