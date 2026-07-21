# ChatGPT Data-Driven UI Automation

A Playwright + pytest suite that reads test questions from an Excel
file, asks each one to ChatGPT, and grades the response by asking
ChatGPT itself whether the answer matches what was expected. Results
are written back into the same Excel file, and each run produces an
HTML report with logs and failure screenshots.

## Quick start

```bash
python scripts/save_login_session.py   # one-time, from a normal network - see below
python scripts/verify_selectors.py     # confirms the page structure before a real run
pytest
```

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

The versions in `requirements.txt` are the ones this was built and
tested against. On a very recent Python (3.13+), one of the pinned
dependencies may try to compile from source and fail if you don't have C
build tools installed. If that happens, installing the packages
unpinned works fine and pulls versions with prebuilt wheels:

```bash
pip install playwright pytest pytest-html openpyxl
```

### Log in once

Scripting credential entry against ChatGPT's login form directly is
deliberately avoided - it's the kind of thing that risks getting an
account flagged, and it wouldn't make the suite any more automated,
just more fragile. Instead, log in manually one time and the browser
profile is reused on every run after that:

```bash
python scripts/save_login_session.py
```

A browser window opens. Log in as you normally would, including any
verification step, then come back to the terminal and press Enter once
your account is visibly signed in (name or chat history showing, not
the "Log in" prompt). This creates `auth/chrome_profile/`, a persistent
Chrome profile, which is gitignored since it holds live session data.

Because that profile is gitignored, a fresh clone has no saved session -
so anyone running this signs in with their own ChatGPT account at this
step. The assignment allows using your own account, and nothing about
the login is shared or committed.

A persistent profile is used rather than exporting cookies into a
separate session, because Cloudflare's clearance cookie is bound to the
specific browser instance that earned it - copying it into a different
browser process gets re-challenged. Reusing the exact same profile on
every run avoids that mismatch entirely.

**Note on network:** the login step should be run from an ordinary
residential or mobile connection rather than a cloud dev environment
(GitHub Codespaces, most CI runners, most VPS providers). Cloudflare
scores requests partly on IP reputation, and datacenter IP ranges score
as high-risk independent of the browser configuration - this can
surface as a `403` on the login request itself. Once `auth/chrome_profile/`
exists, it can be copied to wherever the suite actually needs to run;
the automated test run makes far fewer requests against an
already-authenticated session and is much less exposed to this.

### Verify the page structure before a real run

```bash
python scripts/verify_selectors.py
```

Checks the prompt textbox, send button, and new chat link against the
live page and reports which selector matched (or the full list tried,
if none did). Worth running once after setup and again anytime the
suite starts failing across the board - it separates "the page changed"
from "something else broke" immediately.

## Running the suite

```bash
pytest
```

Reads every row from `data/TestData.xlsx`, asks ChatGPT each question,
validates the answer, writes the result back into the same file, and
generates `reports/report.html`.

Run a single test case:

```bash
pytest tests/test_chatgpt_qa.py -k TC001
```

Run just the unit tests (no browser needed):

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

**Page Object Model.** `ChatPage` is the only page object, since this is
effectively a single-page app - there wasn't a second logical page
worth splitting out.

**Selectors use a fallback list per element rather than one hardcoded
value.** `BasePage.find_first_match()` tries each variant in order and
raises a distinct `ElementNotFoundError` naming exactly what it was
looking for if none match. chatgpt.com's DOM shifts more often than
most production apps this pattern gets used on, so a stale selector
should mean adding one more variant to a list, not rewriting the page
object.

**Excel read and write are separate modules.** A failure reading test
data should stop the whole run before anything happens. A failure
writing one row's result shouldn't take down the rest of the suite.
Splitting them keeps those two failure modes independent.

**The validation prompt forces a `MATCH` / `NO_MATCH` first line.**
Free-form grading text is hard to parse reliably, so the prompt asks
for a fixed keyword up front with reasoning after it - the parsing
logic doesn't have to guess at intent. If ChatGPT doesn't return a
clean verdict, the test is marked FAIL rather than guessed as PASS: a
false failure gets noticed and re-checked, a false pass doesn't.

## Testing strategy

The Excel utilities and the answer validator's parsing logic have unit
tests that don't need a browser - they run in well under a second and
are what gets exercised on every small change during development. The
Excel tests use a temp file per test rather than the real
`TestData.xlsx`, and the validator tests mock `ChatPage` so the parsing
logic can be checked against known ChatGPT response shapes, including a
malformed one, without needing a live session.

The end-to-end suite (`test_chatgpt_qa.py`) is the one part that
genuinely needs a browser and a real ChatGPT session, since validating
real UI behaviour has no substitute for running against the real UI.

## Notes on running against the live site

Automating a Cloudflare-protected, authentication-gated app like
chatgpt.com surfaces a few real-world problems that a simpler target
wouldn't. This section documents the ones worth knowing about and how
each is handled, since they're the parts most likely to trip up someone
running this for the first time.

### Authentication

The suite never scripts the login form. A single manual login is done
once via `scripts/save_login_session.py`, which stores a persistent
Chrome profile under `auth/chrome_profile/`. Every run after that reuses
that profile, so the automated tests start already signed in.

An earlier approach exported session cookies from a normal browser and
loaded them into the automated browser via Playwright's `storage_state`.
That did not work, for a specific reason worth understanding:
Cloudflare's clearance cookie (`cf_clearance`) is bound to the browser
instance that earned it - its TLS and JavaScript fingerprint, not just
the cookie value. Replaying that cookie inside a different browser
process is detected as a mismatch and re-challenged. Reusing the exact
same profile the login happened in avoids this entirely, because it is
genuinely the same browser fingerprint on every run rather than a copy
of one.

### The Cloudflare challenge, and how it was resolved

The most involved problem was getting past Cloudflare's bot check to
reach a logged-in session in the first place. It showed up in three
distinct stages, each needing its own fix:

1. **The automation banner.** Playwright launches Chromium with an
   automation flag that Cloudflare's Turnstile check detects directly -
   the browser shows a "Chrome is being controlled by automated test
   software" banner, and the "Verify you are human" checkbox spins
   forever without ever clearing. Fixed by launching with
   `--disable-blink-features=AutomationControlled` and removing the
   `--enable-automation` default arg (see `BROWSER_LAUNCH_ARGS` and
   `BROWSER_IGNORE_DEFAULT_ARGS` in `config/settings.py`). This removed
   the banner and let the checkbox respond.

2. **The datacenter IP block.** Even with the automation signals hidden,
   running the login from a cloud dev environment (GitHub Codespaces)
   returned a hard `403 Forbidden` with a `Cf-Mitigated: challenge`
   response header on the request to chatgpt.com itself - Cloudflare
   refusing the connection before the page even rendered. This is IP
   reputation: Cloudflare scores datacenter and cloud IP ranges as
   high-risk regardless of how the browser is configured, and no
   browser-side change gets around it. The fix was environmental, not
   code: run the one-time login step from an ordinary residential or
   mobile network instead. From a normal connection the challenge
   cleared and a real logged-in session was established.

3. **Guest-mode false positives during login detection.** ChatGPT's
   signed-out landing page still shows a working chat textbox and
   several "Log in" prompts, so an early version of the login script
   mistook the guest page for a logged-in session and saved a profile
   that wasn't actually authenticated. The login script now confirms the
   signed-in state before saving (checking that the "Log in" button is
   gone), and prints a diagnostic snapshot so the state is unambiguous.

Once the login step is done from a normal network, the resulting
`auth/chrome_profile/` can be copied to wherever the suite runs. The
automated test run makes far fewer requests against an already-
authenticated session, so it is much less exposed to the challenge than
a fresh login attempt is.

### Response completion and dynamic elements

ChatGPT streams its responses token by token, so the suite can't just
read the page immediately after sending. `_wait_for_response` waits for
a new assistant message to appear, then for the stop-generating button
to disappear (ChatGPT's signal that streaming is done), with a fallback
for short answers that finish before that button is even observable.

Starting a new chat for the validation step navigates directly to the
homepage rather than clicking the sidebar link, because the sidebar's
animation intermittently intercepted the click and caused timeouts. The
link only points to `/` anyway, so direct navigation gets the same
result reliably.

## Assumptions and known limitations

- **Login is manual, everything after it is not.** This is the one
  deliberate exception to "runs without manual intervention," and it's
  intentional - see "Log in once" above.
- **The login step should run from a normal network, not a cloud dev
  environment.** See the network note above.
- **Sequential, not parallel.** All test cases run against one shared
  ChatGPT session in order. Parallelizing would mean juggling multiple
  sessions against the same account, which isn't worth the complexity
  for a handful of test cases.
- **Selectors carry a fallback list rather than a single hardcoded
  value**, since chatgpt.com's DOM changes fairly often. Run
  `scripts/verify_selectors.py` on a fresh checkout to catch anything
  stale before it surfaces as a confusing test failure.
- **The Excel file is the source of truth for results**, updated in
  place rather than duplicated into a separate output file, since the
  assignment asks for `TestData.xlsx` itself to come back updated.
- **A test case is marked FAIL if the validation step returns anything
  unexpected** (timeout, unparseable response, etc.), on the basis that
  a failure that gets double-checked by a human is safer than a pass
  that doesn't.

## Screenshots

Screenshots are only captured when a test fails, saved to
`screenshots/` with the test name and timestamp, and referenced in the
HTML report. Nothing is captured for passing runs.
