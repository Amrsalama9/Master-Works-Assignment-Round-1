"""
Opens a real browser window using a persistent profile directory. You
log in to ChatGPT there, then come back and confirm here before it
saves. Automated login detection was tried and kept getting fooled by
ChatGPT's guest mode, which shows a working chat textbox and several
"Log in" prompts even when signed out - it's not a reliable signal on
its own. This now shows you a diagnostic snapshot of the page and asks
you to confirm what you see, since you can look at the actual browser
window directly.

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

        print("Browser launched.")
        print("Log in to ChatGPT in the window - use the actual 'Log in' button,")
        print("enter your credentials, and complete any verification step.")
        print()
        print("Once you can see your account (name, avatar, or email showing")
        print("somewhere on the page, and the 'Log in' / 'Sign up' buttons gone),")
        input("come back here and press Enter...")

        page.wait_for_timeout(1000)
        title = page.title()
        text_sample = page.inner_text("body")[:250].replace("\n", " ")
        still_shows_login_button = page.get_by_role("button", name="Log in").count() > 0

        print()
        print(f"Page title: {title}")
        print(f"Visible text: {text_sample}")
        print(f"'Log in' button still present: {still_shows_login_button}")
        print()

        if still_shows_login_button:
            print("This still looks like a signed-out page - a 'Log in' button")
            print("was found. If you're actually logged in and this is wrong,")
            print("type 'y' to save anyway. Otherwise fix the login and rerun.")
            answer = input("Save this profile anyway? [y/N]: ").strip().lower()
            if answer != "y":
                context.close()
                print("Not saved. Run this script again once logged in.")
                sys.exit(1)

        context.close()
        print(f"Profile saved to {PROFILE_DIR}")


if __name__ == "__main__":
    main()
