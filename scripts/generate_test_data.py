"""
Run once to (re)create data/TestData.xlsx with the base test cases from
the assignment. Not part of the test run itself - this is a setup
convenience, kept separate so the test suite never accidentally
overwrites someone's edited test data.

Usage: python scripts/generate_test_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook

from config.settings import (
    TEST_DATA_PATH,
    COLUMN_TEST_ID,
    COLUMN_QUESTION,
    COLUMN_EXPECTED_ANSWER,
    COLUMN_ACTUAL_ANSWER,
    COLUMN_RESULT,
)

BASE_TEST_CASES = [
    ("TC001", "What is the capital of Saudi Arabia?", "Riyadh"),
    ("TC002", "What is the capital of India?", "New Delhi"),
    ("TC003", "What is 10 + 20?", "30"),
]


def main():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "TestData"

    sheet.append(
        [COLUMN_TEST_ID, COLUMN_QUESTION, COLUMN_EXPECTED_ANSWER, COLUMN_ACTUAL_ANSWER, COLUMN_RESULT]
    )

    for test_id, question, expected_answer in BASE_TEST_CASES:
        sheet.append([test_id, question, expected_answer, "", ""])

    TEST_DATA_PATH.parent.mkdir(exist_ok=True)
    workbook.save(TEST_DATA_PATH)
    print(f"Wrote {len(BASE_TEST_CASES)} test cases to {TEST_DATA_PATH}")


if __name__ == "__main__":
    main()
