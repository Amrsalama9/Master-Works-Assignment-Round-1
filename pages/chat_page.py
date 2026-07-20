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
    periodically. These selectors were correct at the time this was
    written but are the most likely thing to need updating if the suite
    starts failing - check the actual page structure with the Playwright
    inspector before assuming the automation logic itself is broken.
    """

    PROMPT_TEXTBOX = "#prompt-textarea"
    SEND_BUTTON = "[data-testid='send-button']"
    STOP_GENERATING_BUTTON = "[data-testid='stop-button']"
    ASSISTANT_MESSAGE = "[data-message-author-role='assistant']"
    NEW_CHAT_LINK = "a[href='/']"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self):
        self.page.goto(CHATGPT_URL)
        self.wait_for_visible(self.PROMPT_TEXTBOX)

    def start_new_chat(self):
        self.page.locator(self.NEW_CHAT_LINK).first.click()
        self.wait_for_visible(self.PROMPT_TEXTBOX)

    def ask(self, question: str) -> str:
        """
        Sends a question and returns the assistant's response text once
        generation has finished.
        """
        message_count_before = self.page.locator(self.ASSISTANT_MESSAGE).count()

        textbox = self.wait_for_visible(self.PROMPT_TEXTBOX)
        textbox.first.click()
        textbox.first.fill(question)
        self.page.locator(self.SEND_BUTTON).click()

        logger.info("Sent prompt: %s", question)

        self._wait_for_response(message_count_before)

        response_locator = self.page.locator(self.ASSISTANT_MESSAGE).last
        response_text = response_locator.inner_text().strip()

        logger.info("Received response (%d chars)", len(response_text))
        return response_text

    def _wait_for_response(self, message_count_before: int):
        """
        Waits for a new assistant message to appear, then waits for the
        stop-generating button to disappear, which is ChatGPT's signal
        that streaming has finished. Polling on message count first
        avoids a race where we check for the stop button before
        generation has even started.
        """
        self.page.locator(self.ASSISTANT_MESSAGE).nth(message_count_before).wait_for(
            state="visible", timeout=RESPONSE_TIMEOUT_MS
        )

        try:
            self.wait_for_hidden(self.STOP_GENERATING_BUTTON, timeout_ms=RESPONSE_TIMEOUT_MS)
        except Exception:
            # Short answers can finish generating before we even get a
            # chance to see the stop button appear. That's fine - the
            # assistant message being visible already tells us it's done.
            logger.info("Stop-generating button never observed, response was likely fast")
