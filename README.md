# ChatGPT Data-Driven UI Automation

Automates asking ChatGPT a set of questions from an Excel file, capturing
its answers, and grading each one by asking ChatGPT itself whether the
actual answer matches what was expected. Results get written back into
the same Excel file, and a run produces an HTML report with logs and
screenshots for anything that failed.

## Known limitation: run the login step from a normal network

The one manual step in this framework - logging in once via
`scripts/save_login_session.py` - needs to happen from an ordinary
residential or mobile network connection, not from a cloud dev
environment (GitHub Codespaces, most CI runners, most VPS providers).

This isn't a bug in the automation. Cloudflare, which sits in front of
chatgpt.com, scores requests partly on the reputation of the IP range
they come from, and cloud/datacenter IP ranges score as high-risk
regardless of what the browser looks like. During development, running
`save_login_session.py` from a Codespace hit a hard `403 Forbidden` with
a `Cf-Mitigated: challenge` response header directly on the login
request - Cloudflare blocking the connection before the page even
rendered, independent of the browser configuration.

The fix is straightforward and doesn't touch any code: run
`save_login_session.py` once from a normal network (home wifi, a phone
hotspot, any non-datacenter connection), which creates
`auth/chrome_profile/`. Copy that folder into wherever the suite will
actually run. The automated test run itself - `pytest` - is much less
likely to hit the same wall, since it's making a smaller number of
requests using an already-authenticated session rather than a fresh
Cloudflare challenge from an unrecognized browser.

## Before running for review

`scripts/save_login_session.py` (from a normal network - see above),
then `scripts/verify_selectors.py`, then `pytest`, in that order. If
`verify_selectors.py` reports a FAIL, check whether the page title is
"Just a moment..." (a Cloudflare challenge - see the limitation above)
before assuming a selector is stale.

## Prerequisites

- Python 3.10+
- A ChatGPT account (free tier is fine)
- Google Chrome or Chromium (Playwright installs its own copy, see below)

## Project setup

```bash
git clone https://github.com/Amrsalama9/Master-Works-Assignment-Round-1.git
cd Master-Works-Assignment-Round-1

python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows

pip install -r requirements.txt
playwright install chromium
```

### Log in once

Automating the ChatGPT login form directly is deliberately avoided here.
Scripting credential entry against a Cloudflare-protected login page is
the kind of thing that gets an account flagged, and it would make the
whole suite less reliable, not more automated. Instead, log in manually
one time and the browser session gets saved for every run after that:

```bash
python scripts/save_login_session.py
```

A browser window opens, you log in as you normally would (including any
2FA and any Cloudflare check). Come back to the terminal and press Enter
once you can see the actual chat screen. This creates
`auth/chrome_profile/`, a persistent browser profile, which is gitignored.

This is a real Chrome profile directory, not just a cookie file -
Cloudflare's clearance cookie is tied to the exact browser fingerprint
that earned it, so exporting cookies out of one browser and importing
them into another (even another Chromium instance) gets re-challenged.
Reusing the same profile on every run sidesteps that entirely.

### Verify selectors before a real run

```bash
python scripts/verify_selectors.py
```

Checks the prompt textbox, send button, and new chat link against the
live page and prints PASS/FAIL per element, showing either the selector
that worked or the full list that was tried. Worth running once after
setup, and again first if the suite ever starts failing across the
board - it separates "the DOM changed" from "the logic broke"
immediately instead of after watching a test time out.

## Running the suite

```bash
pytest
```

This reads every row from `data/TestData.xlsx`, asks ChatGPT each
question, validates the answer, writes the result back into the same
file, and generates `reports/report.html`.

To run a single test case:

```bash
pytest tests/test_chatgpt_qa.py -k TC001
```

To run just the unit tests (no browser needed):

```bash
pytest tests/test_excel_utils.py tests/test_answer_validator.py
```

## Framework architecture

```
config/       constants - paths, timeouts, Excel column names
pages/        Page Object Model - ChatPage wraps the chat UI
utils/        Excel read/write, logging
validation/   the ChatGPT-grades-ChatGPT comparison logic
tests/        conftest.py (fixtures, screenshot-on-failure) + the suite
scripts/      one-off setup scripts (save session, regenerate TestData.xlsx)
data/         TestData.xlsx
auth/         chrome_profile/ (gitignored)
reports/      pytest-html output
screenshots/  captured on test failure
logs/         one log file per run
```

**Page Object Model** - `ChatPage` is the only page object because this
is effectively a single-page app; there wasn't a second logical page to
justify splitting further.

**Each element has a list of selector variants, not one hardcoded
selector.** `BasePage.find_first_match()` tries each in order and raises
a distinct `ElementNotFoundError` naming exactly what it was looking for
if none match. chatgpt.com's DOM shifts more often than most production
apps this pattern gets used on, and a single stale selector shouldn't
mean rewriting `chat_page.py` from scratch - it should mean adding one
more variant to a list.

**Excel read and write are separate modules.** A failure reading test
data should stop the whole run before anything happens. A failure
writing one row's result shouldn't take down the rest of the suite.
Splitting them keeps those two failure modes independent.

**The validation prompt forces a `MATCH` / `NO_MATCH` first line.** Free-form
grading text is hard to parse reliably. Asking for a fixed keyword up
front, with reasoning after it, means the parsing logic doesn't have to
guess at intent. If ChatGPT doesn't return a clean verdict, the test is
marked FAIL rather than guessed as PASS - a false failure gets noticed
and re-checked, a false pass doesn't.

**Persistent profile instead of exported cookies.** The first version of
this used Playwright's `storage_state` to export cookies from a manual
login and replay them into the automated browser. That didn't hold up -
Cloudflare's clearance cookie is bound to the specific browser instance
it was issued to, and importing it into a different Chromium process
just got re-challenged with a "Just a moment..." page. Logging in once
inside the exact same profile the automated runs reuse (via
`launch_persistent_context`) avoids that mismatch, because it's
genuinely the same browser fingerprint every time, not a copy of one.
Login happens once, by hand, inside that profile; the automated run
never touches the login form.

## Testing strategy

The Excel utilities and the answer validator's parsing logic have unit
tests that don't need a browser at all - they run in well under a
second and are what actually gets exercised on every small change during
development. The Excel tests use a temp file per test rather than the
real `TestData.xlsx`, and the validator tests mock `ChatPage` so the
parsing logic can be checked against known ChatGPT response shapes,
including a malformed one, without needing a live session.

The end-to-end suite (`test_chatgpt_qa.py`) is the one thing that
genuinely needs a browser and a real ChatGPT session, since that's the
actual scope of the assignment - there's no way to validate real UI
behaviour without running against the real UI.

## Assumptions and known limitations

- **Login is manual, everything after it is not.** This is the one
  deliberate exception to "runs without manual intervention," and it's
  intentional - see the reasoning above.
- **The login step must run from a normal network, not a cloud dev
  environment.** See "Known limitation" at the top of this file -
  confirmed during development against GitHub Codespaces specifically,
  which got a `403` directly from Cloudflare on the login request.
- **Sequential, not parallel.** All test cases run against one shared
  ChatGPT session in order. Parallelizing would mean juggling multiple
  sessions against the same account, which isn't worth the complexity
  for a handful of test cases.
- **Selectors were not confirmed against a live session at write time**
  (this was built without network access to chatgpt.com) and use a
  fallback list per element rather than a single hardcoded selector, so
  minor DOM changes are less likely to break the whole suite. Run
  `scripts/verify_selectors.py` before trusting a fresh checkout -
  that's the fast way to catch anything that's actually stale before
  it shows up as a confusing test failure.
- **The Excel file is the source of truth for results**, updated in
  place rather than duplicated into a separate output file, since the
  assignment asks for `TestData.xlsx` itself to come back updated.
- **A test case is marked FAIL if the validation step returns anything
  unexpected** (timeout, unparseable response, etc.), on the basis that
  a failure that gets double-checked by a human is safer than a pass
  that doesn't.

## Screenshots

Screenshots are only captured when a test fails, saved to
`screenshots/` with the test name and timestamp, and referenced in
`reports/report.html`. Nothing is captured for passing runs.
