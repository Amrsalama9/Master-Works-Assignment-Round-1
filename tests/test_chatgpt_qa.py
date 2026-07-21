import pytest

from config.settings import TEST_DATA_PATH
from utils.excel_reader import read_test_cases
from utils.excel_writer import update_test_result
from utils.retry import retry_on_exception
from validation.answer_validator import AnswerValidator
from utils.logger import get_logger

logger = get_logger(__name__)

test_cases = read_test_cases(TEST_DATA_PATH)


@pytest.mark.parametrize(
    "test_case",
    test_cases,
    ids=[tc.test_id for tc in test_cases],
)
def test_chatgpt_answer(test_case, chat_page):
    """
    For each row in TestData.xlsx: ask the question, capture the answer,
    then have ChatGPT itself judge whether it matches the expected
    answer. The Excel file is updated with both the actual answer and
    the result regardless of pass or fail, so the deliverable always
    reflects the latest run.

    The two live calls (ask, validate) are retried once on failure - a
    single slow response or momentary UI hiccup shouldn't fail a test
    that would pass on a second attempt. A persistent failure still
    surfaces, since the retry re-raises after its last attempt.
    """
    logger.info("Running %s: %s", test_case.test_id, test_case.question)

    actual_answer = retry_on_exception(lambda: chat_page.ask(test_case.question))

    validator = AnswerValidator(chat_page)
    result = retry_on_exception(
        lambda: validator.validate(
            expected_answer=test_case.expected_answer,
            actual_answer=actual_answer,
        )
    )

    update_test_result(
        TEST_DATA_PATH,
        row_number=test_case.row_number,
        actual_answer=actual_answer,
        result=result,
    )

    assert result == "PASS", (
        f"{test_case.test_id} failed. "
        f"Expected: {test_case.expected_answer!r}, Actual: {actual_answer!r}"
    )
