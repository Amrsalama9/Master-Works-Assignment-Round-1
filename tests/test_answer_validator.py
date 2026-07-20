from unittest.mock import Mock

from validation.answer_validator import AnswerValidator


def _validator_with_response(response_text):
    chat_page = Mock()
    chat_page.ask.return_value = response_text
    return AnswerValidator(chat_page), chat_page


def test_validate_returns_pass_when_chatgpt_says_match():
    # Arrange
    validator, chat_page = _validator_with_response(
        "MATCH\nBoth answers name the same city as the capital."
    )

    # Act
    result = validator.validate(expected_answer="Riyadh", actual_answer="The capital is Riyadh.")

    # Assert
    assert result == "PASS"
    chat_page.start_new_chat.assert_called_once()


def test_validate_returns_fail_when_chatgpt_says_no_match():
    # Arrange
    validator, _ = _validator_with_response(
        "NO_MATCH\nThe expected answer refers to a different city."
    )

    # Act
    result = validator.validate(expected_answer="Riyadh", actual_answer="Jeddah")

    # Assert
    assert result == "FAIL"


def test_validate_fails_closed_when_response_is_unparseable():
    # Arrange - ChatGPT ignored the requested format
    validator, _ = _validator_with_response("These answers look similar to me.")

    # Act
    result = validator.validate(expected_answer="30", actual_answer="thirty")

    # Assert
    assert result == "FAIL"
