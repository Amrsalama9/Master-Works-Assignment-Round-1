"""
Run this after save_login_session.py and before the real test suite.
Opens chatgpt.com using the saved persistent profile and checks every
selector this framework depends on, printing a clear PASS/FAIL per
element instead of letting a stale selector - or a failed login -
surface as a confusing failure buried inside a test run.

This exists because the automation was built and reviewed without live
access to chatgpt.com from the development environment - the selectors
are based on ChatGPT's known DOM conventions, not confirmed against the
site at write time. This script is the fast way to confirm they still
hold, and to see exactly what's on the page if they don't.

Usage: python scripts/verify_selectors.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from config.settings import (
    CHATGPT_URL,
    PROFILE_DIR,
    SCREENSHOTS_DIR,
    BROWSER_LAUNCH_ARGS,
    BROWSER_IGNORE_DEFAULT_ARGS,
)
from pages.chat_page import ChatPage


CHECKS = [
    ("Prompt textbox", ChatPage.PROMPT_TEXTBOX_SELECTORS),
    ("Send button", ChatPage.SEND_BUTTON_SELECTORS),
    ("New chat link", ChatPage.NEW_CHAT_SELECTORS),
]


def check_selector_group(page, label, selectors):
    for selector in selectors:
        count = page.locator(selector).count()
        if count > 0:
            print(f"  PASS  {label}: matched '{selector}' ({count} element(s))")
            return True
    print(f"  FAIL  {label}: none of these matched: {selectors}")
    return False


def main():
    if not PROFILE_DIR.exists():
        print(f"No saved login profile found at {PROFILE_DIR}.")
        print("Run scripts/save_login_session.py first.")
        sys.exit(1)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=BROWSER_LAUNCH_ARGS,
            ignore_default_args=BROWSER_IGNORE_DEFAULT_ARGS,
        )
        page = context.new_page()
        page.goto(CHATGPT_URL)
        page.wait_for_timeout(3000)  # let the app finish its initial render

        print(f"Checking selectors against {CHATGPT_URL}\n")
        print(f"Page title: {page.title()}")
        print(f"Current URL: {page.url}")

        page_text_sample = page.inner_text("body")[:300].replace("\n", " ")
        print(f"Visible text sample: {page_text_sample}\n")

        SCREENSHOTS_DIR.mkdir(exist_ok=True)
        screenshot_path = SCREENSHOTS_DIR / "verify_selectors_page.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved to {screenshot_path}\n")

        if "Just a moment" in page.title():
            print(
                "This is a Cloudflare challenge page, not the real ChatGPT app. "
                "The profile likely isn't logged in yet, or the challenge wasn't "
                "cleared. Re-run scripts/save_login_session.py and make sure you "
                "reach the actual chat screen before pressing Enter.\n"
            )

        results = [check_selector_group(page, label, selectors) for label, selectors in CHECKS]

        print()
        if all(results):
            print("All core selectors matched. The suite should be safe to run.")
        else:
            print(
                "One or more selectors did not match. Inspect the live page "
                "(playwright codegen chatgpt.com, or the browser devtools) and "
                "update the matching list in pages/chat_page.py before running "
                "the test suite - a run against a broken selector will just "
                "time out on every test case."
            )

        context.close()
        sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
