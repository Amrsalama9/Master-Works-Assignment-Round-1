"""
Run this once before running the suite for the first time, or whenever
the saved session expires. Opens a real browser window, you log in to
ChatGPT by hand (including any 2FA or Cloudflare check), then press
Enter in the terminal and the session gets saved to auth/storage_state.json.

Everything after this is fully automated - this script is the one
deliberate manual step the assignment allows for.

Usage: python scripts/save_login_session.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from config.settings import CHATGPT_URL, STORAGE_STATE_PATH


def main():
    STORAGE_STATE_PATH.parent.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(CHATGPT_URL)

        input(
            "Log in to ChatGPT in the browser window, then come back here "
            "and press Enter to save the session..."
        )

        context.storage_state(path=str(STORAGE_STATE_PATH))
        print(f"Session saved to {STORAGE_STATE_PATH}")

        browser.close()


if __name__ == "__main__":
    main()
