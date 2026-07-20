"""
Run this once before running the suite for the first time, or whenever
the login stops being recognized. Opens a real browser window using a
persistent profile directory, you log in to ChatGPT by hand (including
any 2FA or Cloudflare check), then press Enter in the terminal.

This uses a persistent Chrome profile rather than exporting/importing
cookies. Cloudflare's clearance cookie is tied to the exact browser
fingerprint it was issued to - a cookie exported from one browser and
imported into another gets re-challenged. Logging in once inside this
exact profile, and reusing the same profile on every subsequent run,
avoids that problem entirely.

Everything after this is fully automated - this script is the one
deliberate manual step the assignment allows for.

Usage: python scripts/save_login_session.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from config.settings import CHATGPT_URL, PROFILE_DIR


def main():
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
        )
        page = context.new_page()
        page.goto(CHATGPT_URL)

        input(
            "Log in to ChatGPT in the browser window, then come back here "
            "and press Enter once you can see the chat screen..."
        )

        context.close()
        print(f"Profile saved to {PROFILE_DIR}")


if __name__ == "__main__":
    main()
