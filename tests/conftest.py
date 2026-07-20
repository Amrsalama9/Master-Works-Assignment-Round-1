from datetime import datetime

import pytest
from playwright.sync_api import sync_playwright

from config.settings import (
    STORAGE_STATE_PATH,
    SCREENSHOTS_DIR,
    HEADLESS,
    SLOW_MO_MS,
)
from pages.chat_page import ChatPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def browser():
    if not STORAGE_STATE_PATH.exists():
        pytest.exit(
            f"No saved login session found at {STORAGE_STATE_PATH}. "
            f"Log in to chatgpt.com manually once and save the session - "
            f"see the README's 'Prerequisites' section."
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO_MS)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(storage_state=str(STORAGE_STATE_PATH))
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def chat_page(page):
    chat = ChatPage(page)
    chat.open()
    return chat


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Captures a screenshot when a test fails, saved next to the log files
    so both can be checked together. Uses the 'page' fixture directly
    rather than chat_page since a failure can happen before the chat
    page finishes loading.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page_fixture = item.funcargs.get("page")
        if page_fixture is None:
            return

        SCREENSHOTS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = SCREENSHOTS_DIR / f"{item.name}_{timestamp}.png"

        try:
            page_fixture.screenshot(path=str(screenshot_path))
            logger.error("Test %s failed, screenshot saved to %s", item.name, screenshot_path)
        except Exception as screenshot_error:
            logger.error("Test %s failed, could not capture screenshot: %s", item.name, screenshot_error)
