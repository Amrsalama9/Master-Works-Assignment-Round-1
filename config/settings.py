"""
Central place for anything that would otherwise be a magic number or a
hardcoded path scattered across the codebase.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Data
TEST_DATA_PATH = ROOT_DIR / "data" / "TestData.xlsx"

# Auth
# A persistent browser profile, not a cookie file. Cloudflare's
# cf_clearance cookie is tied to the exact browser fingerprint it was
# issued to, so exporting cookies from one browser and importing them
# into Playwright's Chromium just gets re-challenged. Logging in once
# inside this exact profile, and reusing the same profile on every run,
# avoids that mismatch entirely.
PROFILE_DIR = ROOT_DIR / "auth" / "chrome_profile"

# Output
SCREENSHOTS_DIR = ROOT_DIR / "screenshots"
LOGS_DIR = ROOT_DIR / "logs"
REPORTS_DIR = ROOT_DIR / "reports"

# Application under test
CHATGPT_URL = "https://chatgpt.com"

# Timeouts (milliseconds, Playwright convention)
DEFAULT_TIMEOUT_MS = 15_000
RESPONSE_TIMEOUT_MS = 60_000  # ChatGPT can take a while to finish a long answer

# Browser
# Cloudflare is more likely to challenge a headless browser than a
# headed one, even with a legitimate persistent profile. Default to
# headed - it still runs unattended fine under Xvfb, it just needs a
# display to render onto, not a human watching it.
HEADLESS = False
SLOW_MO_MS = 0

# Excel column headers, kept as constants so a typo doesn't silently break
# the read/write utilities.
COLUMN_TEST_ID = "Test ID"
COLUMN_QUESTION = "Question"
COLUMN_EXPECTED_ANSWER = "Expected Answer"
COLUMN_ACTUAL_ANSWER = "Actual Answer"
COLUMN_RESULT = "Result"

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
