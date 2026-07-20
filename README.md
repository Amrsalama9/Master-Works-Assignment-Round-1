# ChatGPT Data-Driven UI Automation

Automates asking ChatGPT a set of questions from an Excel file, capturing
its answers, and grading each one by asking ChatGPT itself whether the
actual answer matches what was expected. Results get written back into
the same Excel file, and a run produces an HTML report with logs and
screenshots for anything that failed.

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
2FA), come back to the terminal and press Enter. This writes
`auth/storage_state.json`, which is gitignored - it's a live session
token and shouldn't be committed.

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
auth/         storage_state.json (gitignored)
reports/      pytest-html output
screenshots/  captured on test failure
logs/         one log file per run
```

**Page Object Model** - `ChatPage` is the only page object because this
is effectively a single-page app; there wasn't a second logical page to
justify splitting further.

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

**Session reuse instead of scripted login.** Playwright's `storage_state`
captures cookies and local storage from one authenticated session and
replays them on every subsequent browser context. Login happens once,
by hand; the automated run never touches the login form.

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
- **Sequential, not parallel.** All test cases run against one shared
  ChatGPT session in order. Parallelizing would mean juggling multiple
  sessions against the same account, which isn't worth the complexity
  for a handful of test cases.
- **Selectors may need updating.** ChatGPT's frontend changes its DOM
  periodically. If the suite starts failing on every test at the same
  step, check `pages/chat_page.py`'s selectors against the live page
  before assuming the automation logic itself broke.
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
