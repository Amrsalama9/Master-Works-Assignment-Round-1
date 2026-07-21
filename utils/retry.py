import time

from utils.logger import get_logger

logger = get_logger(__name__)


def retry_on_exception(func, attempts: int = 2, delay_seconds: float = 3.0):
    """
    Runs func and, if it raises, waits and tries once more. Meant for the
    live browser calls against ChatGPT, where a single slow response or a
    momentary UI hiccup can fail an operation that would succeed on a
    second try. Deliberately kept to a small number of attempts - this is
    for genuinely transient failures, not for masking a real problem by
    hammering a broken page.

    Re-raises the last exception if every attempt fails, so a persistent
    failure still surfaces clearly instead of being swallowed.
    """
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as error:
            last_error = error
            if attempt < attempts:
                logger.warning(
                    "Attempt %d/%d failed (%s), retrying in %.0fs",
                    attempt,
                    attempts,
                    type(error).__name__,
                    delay_seconds,
                )
                time.sleep(delay_seconds)

    raise last_error
