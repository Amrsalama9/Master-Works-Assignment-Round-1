from playwright.sync_api import Page

from config.settings import CHATGPT_URL, RESPONSE_TIMEOUT_MS
from pages.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ChatPage(BasePage):
    """
    Wraps the parts of chatgpt.com this suite actually touches: sending a
    prompt, reading the response back, and starting a new chat.

    Note on selectors: ChatGPT's frontend changes its DOM structure
    periodically, more often than most production apps this team has
    automated. Each element below has a short list of known selector
    variants rather than a single hardcoded one, so a minor markup change
    doesn't necessarily break the whole suite. If ALL variants for an
    element fail, ElementNotFoundError says exactly which element and
    which selectors were tried - check that against the live page before
    assuming anything else is wrong.
    """

    PROMPT_TEXTBOX_SELECTORS = [
        "#prompt-textarea",
        "div[contenteditable='true'][id='prompt-textarea']",
        "textarea[data-testid='prompt-textarea']",
        "div[contenteditable='true']",
    ]

    SEND_BUTTON_SELECTORS = [
        "[data-testid='send-button']",
        "button[aria-label='Send prompt']",
        "button[aria-label*='Send']",
    ]

    STOP_GENERATING_SELECTORS = [
        "[data-testid='stop-button']",
        "button[aria-label='Stop generating']",
        "button[aria-label*='Stop']",
    ]

    ASSISTANT_MESSAGE_SELECTORS = [
        "[data-message-author-role='assistant']",
        "div[data-message-author-role='assistant']",
    ]

    NEW_CHAT_SELECTORS = [
        "a[href='/']",
        "a[data-testid='create-new-chat-button']",
        "button[aria-label='New chat']",
    ]

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self):
        self.page.goto(CHATGPT_URL)
        self.find_first_match("prompt textbox", self.PROMPT_TEXTBOX_SELECTORS)

    def start_new_chat(self):
        new_chat_locator = self.find_first_match("new chat link", self.NEW_CHAT_SELECTORS)
        new_chat_locator.first.click()
        self.find_first_match("prompt textbox", self.PROMPT_TEXTBOX_SELECTORS)

    def ask(self, question: str) -> str:
        """
        Sends a question and returns the assistant's response text once
        generation has finished.
        """
        message_count_before = self._count_assistant_messages()

        textbox = self.find_first_match("prompt textbox", self.PROMPT_TEXTBOX_SELECTORS)
        textbox.first.click()
        textbox.first.fill(question)

        send_button = self.find_first_match("send button", self.SEND_BUTTON_SELECTORS)
        send_button.first.click()

        logger.info("Sent prompt: %s", question)

        self._wait_for_response(message_count_before)

        response_locator = self._assistant_message_locator().last
        response_text = response_locator.inner_text().strip()

        logger.info("Received response (%d chars)", len(response_text))
        return response_text

    def _assistant_message_locator(self):
        for selector in self.ASSISTANT_MESSAGE_SELECTORS:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                return locator
        # Return a locator on the last-tried selector even if empty -
        # callers that need a count of 0 (e.g. before the first message)
        # still need something to call .count() on.
        return self.page.locator(self.ASSISTANT_MESSAGE_SELECTORS[-1])

    def _count_assistant_messages(self) -> int:
        return self._assistant_message_locator().count()

    def _wait_for_response(self, message_count_before: int):
        """
        Waits for a new assistant message to appear, then waits for the
        stop-generating button to disappear, which is ChatGPT's signal
        that streaming has finished. Polling on message count first
        avoids a race where we check for the stop button before
        generation has even started.
        """
        self._assistant_message_locator().nth(message_count_before).wait_for(
            state="visible", timeout=RESPONSE_TIMEOUT_MS
        )

        stop_button_seen = False
        for selector in self.STOP_GENERATING_SELECTORS:
            locator = self.page.locator(selector)
            if locator.count() > 0:
                stop_button_seen = True
                try:
                    locator.first.wait_for(state="hidden", timeout=RESPONSE_TIMEOUT_MS)
                except Exception:
                    logger.warning(
                        "Stop-generating button did not disappear within %sms, "
                        "proceeding anyway - response may be incomplete",
                        RESPONSE_TIMEOUT_MS,
                    )
                break

        if not stop_button_seen:
            # Short answers can finish generating before we even get a
            # chance to see the stop button appear. That's fine - the
            # assistant message being visible already tells us it's done.
            logger.info("Stop-generating button never observed, response was likely fast")
