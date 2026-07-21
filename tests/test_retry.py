import pytest

from utils.retry import retry_on_exception


def test_returns_result_without_retrying_when_first_attempt_succeeds():
    # Arrange
    calls = []

    def succeeds():
        calls.append(1)
        return "ok"

    # Act
    result = retry_on_exception(succeeds)

    # Assert
    assert result == "ok"
    assert len(calls) == 1


def test_retries_once_then_succeeds():
    # Arrange
    calls = []

    def fails_then_succeeds():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("transient")
        return "ok"

    # Act
    result = retry_on_exception(fails_then_succeeds, delay_seconds=0)

    # Assert
    assert result == "ok"
    assert len(calls) == 2


def test_reraises_when_every_attempt_fails():
    # Arrange
    def always_fails():
        raise RuntimeError("persistent")

    # Act / Assert
    with pytest.raises(RuntimeError, match="persistent"):
        retry_on_exception(always_fails, attempts=2, delay_seconds=0)
