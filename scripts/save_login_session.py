"""
Opens a real browser window using a persistent profile directory, then
automatically waits for the actual ChatGPT chat screen to appear -
it does not rely on the human pressing Enter at the right moment. That
timing was the exact thing causing the profile to get saved before login
actually completed. This polls for the real chat UI instead.

Usage: python scripts/save_login_session.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from config.settings import (
    CHATGPT_URL,
    PROFILE_DIR,
    BROWSER_LAUNCH_ARGS,
    BROWSER_IGNORE_DEFAULT_ARGS,
)
from pages.chat_page import ChatPage

WAIT_FOR_LOGIN_MS = 10 * 60 * 1000  # 10 minutes to log in


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=BROWSER_LAUNCH_ARGS,
            ignore_default_args=BROWSER_IGNORE_DEFAULT_ARGS,
        )
        page = context.new_page()
        page.goto(CHATGPT_URL)

        print("Browser launched. Log in to ChatGPT in the window (via noVNC).")
        print("This will wait automatically - no need to press Enter.")
        print("Waiting up to 10 minutes for the chat screen to appear...")

        logged_in = False
        for selector in ChatPage.PROMPT_TEXTBOX_SELECTORS:
            try:
                page.locator(selector).first.wait_for(state="visible", timeout=WAIT_FOR_LOGIN_MS)
                logged_in = True
                break
            except Exception:
                continue

        if logged_in:
            # The textbox alone isn't proof of login - ChatGPT's guest
            # mode shows one too. Check for the "Log in" link that only
            # appears when signed out.
            still_logged_out = page.locator("text=Log in").count() > 0
            if still_logged_out:
                print("A chat textbox is visible, but this still looks like a guest")
                print("session - a 'Log in' link is present. Waiting for real login...")
                logged_in = False
                try:
                    page.locator("text=Log in").first.wait_for(state="hidden", timeout=WAIT_FOR_LOGIN_MS)
                    logged_in = True
                except Exception:
                    logged_in = False

        if not logged_in:
            print("Timed out waiting for the chat screen. Login was not detected.")
            print(f"Current page title: {page.title()}")
            context.close()
            sys.exit(1)

        print("Chat screen detected - login confirmed.")
        context.close()
        print(f"Profile saved to {PROFILE_DIR}")


if __name__ == "__main__":
    main()
