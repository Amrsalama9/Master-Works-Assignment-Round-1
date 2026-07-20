from datetime import datetime

import pytest
from playwright.sync_api import sync_playwright

from config.settings import (
    PROFILE_DIR,
    SCREENSHOTS_DIR,
    HEADLESS,
    SLOW_MO_MS,
    BROWSER_LAUNCH_ARGS,
    BROWSER_IGNORE_DEFAULT_ARGS,
)
from pages.chat_page import ChatPage
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="session")
def browser_context():
    """
    Session-scoped so every test case runs inside the same persistent
    profile and the same browser process, matching how the assignment
    actually works: one logged-in ChatGPT session, used sequentially.
    """
    if not PROFILE_DIR.exists():
        pytest.exit(
            f"No saved login profile found at {PROFILE_DIR}. "
            f"Run scripts/save_login_session.py first - see the README's "
            f"'Prerequisites' section."
        )

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=HEADLESS,
            slow_mo=SLOW_MO_MS,
            args=BROWSER_LAUNCH_ARGS,
            ignore_default_args=BROWSER_IGNORE_DEFAULT_ARGS,
        )
        yield context
        context.close()


@pytest.fixture
def page(browser_context):
    page = browser_context.new_page()
    yield page
    page.close()


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
