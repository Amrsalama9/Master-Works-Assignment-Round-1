import re

from config.settings import RESULT_PASS, RESULT_FAIL
from pages.chat_page import ChatPage
from utils.logger import get_logger

logger = get_logger(__name__)

# ChatGPT is asked to lead with one of these two words so the parsing
# doesn't have to guess intent out of free-form text. Everything after
# that first word is just reasoning for a human reading the transcript.
VERDICT_MATCH = "MATCH"
VERDICT_NO_MATCH = "NO_MATCH"

VALIDATION_PROMPT_TEMPLATE = """You are comparing two answers to the same question to check if they mean the same thing.

Expected answer: {expected_answer}
Actual answer: {actual_answer}

Do these two answers convey the same correct information, even if worded differently, \
one is more detailed, or formatted differently? Minor differences in phrasing, \
capitalization, or extra explanation do not count as a mismatch, as long as the \
core fact or value is the same.

Respond with exactly one word on the first line: {verdict_match} or {verdict_no_match}.
On the next line, give a one-sentence reason for your answer."""


class AnswerValidator:
    """
    Grades an actual answer against an expected answer by asking ChatGPT
    itself, in a fresh chat, whether the two are semantically equivalent.
    """

    def __init__(self, chat_page: ChatPage):
        self.chat_page = chat_page

    def validate(self, expected_answer: str, actual_answer: str) -> str:
        self.chat_page.start_new_chat()

        prompt = VALIDATION_PROMPT_TEMPLATE.format(
            expected_answer=expected_answer,
            actual_answer=actual_answer,
            verdict_match=VERDICT_MATCH,
            verdict_no_match=VERDICT_NO_MATCH,
        )

        response = self.chat_page.ask(prompt)
        return self._parse_verdict(response)

    def _parse_verdict(self, response: str) -> str:
        first_line = response.strip().splitlines()[0] if response.strip() else ""

        if re.search(rf"\b{VERDICT_MATCH}\b", first_line) and not re.search(
            rf"\b{VERDICT_NO_MATCH}\b", first_line
        ):
            return RESULT_PASS

        if re.search(rf"\b{VERDICT_NO_MATCH}\b", first_line):
            return RESULT_FAIL

        # ChatGPT didn't follow the format we asked for. Fail closed
        # rather than guess - a silent false PASS is worse than a test
        # that clearly needs a human to look at it.
        logger.warning("Could not parse a clear verdict from response: %r", response)
        return RESULT_FAIL
