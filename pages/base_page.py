from playwright.sync_api import Page

from config.settings import DEFAULT_TIMEOUT_MS


class ElementNotFoundError(Exception):
    """
    Raised when none of the known selectors for an element match. Kept
    as its own exception type so a stale-selector failure is
    unmistakable in the logs and report, instead of showing up as a
    generic Playwright TimeoutError that looks like a network or timing
    problem.
    """


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

    def find_first_match(self, element_name: str, selectors: list[str], timeout_ms: int = DEFAULT_TIMEOUT_MS):
        """
        Tries each selector in order and returns the first one that
        actually appears on the page. chatgpt.com changes its DOM often
        enough that hardcoding a single selector per element is brittle -
        this gives each element a short list of known variants instead of
        needing a code change every time OpenAI ships a markup tweak.

        Raises ElementNotFoundError with the full list that was tried if
        none of them show up, so whoever is debugging a failed run knows
        immediately this is a selector problem, not a logic bug.
        """
        for selector in selectors:
            locator = self.page.locator(selector)
            try:
                locator.first.wait_for(state="visible", timeout=timeout_ms // len(selectors))
                return locator
            except Exception:
                continue

        raise ElementNotFoundError(
            f"Could not find '{element_name}' on the page. Tried selectors: {selectors}. "
            f"chatgpt.com's DOM likely changed - inspect the live page and update "
            f"pages/chat_page.py."
        )
