"""
tests/test_tools_utils.py
Unit tests for aria_core/tools_utils.py — the calculator (safe AST-based
arithmetic) and the DuckDuckGo web search wrapper.

web_search's network call is mocked (`requests.get`) so these tests are
fast, deterministic, and don't depend on an internet connection or
DuckDuckGo actually being up.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aria_core.tools_utils import calculate, web_search


class TestCalculate(unittest.TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(calculate("2 + 2"), "4")
        self.assertEqual(calculate("10 - 3"), "7")
        self.assertEqual(calculate("6 * 7"), "42")
        self.assertEqual(calculate("847 * 23"), "19481")

    def test_operator_precedence_and_parentheses(self):
        self.assertEqual(calculate("2 + 3 * 4"), "14")
        self.assertEqual(calculate("(2 + 3) * 4"), "20")

    def test_division(self):
        self.assertEqual(calculate("10 / 4"), "2.5")

    def test_power_and_modulo(self):
        self.assertEqual(calculate("2 ** 10"), "1024")
        self.assertEqual(calculate("10 % 3"), "1")

    def test_negative_numbers(self):
        self.assertEqual(calculate("-5 + 3"), "-2")

    def test_division_by_zero_returns_error_string_not_exception(self):
        result = calculate("1 / 0")
        self.assertTrue(result.startswith("Error"))

    def test_invalid_syntax_returns_error_string(self):
        result = calculate("2 + + + ")
        self.assertTrue(result.startswith("Error"))

    def test_rejects_arbitrary_code_execution_attempts(self):
        """The whole point of using ast instead of eval(): none of these
        should ever actually run. Each must come back as a safe error
        string, never raise an uncaught exception or execute anything."""
        dangerous_expressions = [
            "__import__('os').system('echo pwned')",
            "open('/etc/passwd').read()",
            "[x for x in ().__class__.__bases__[0].__subclasses__()]",
            "exec('print(1)')",
            "1; import os",
        ]
        for expr in dangerous_expressions:
            result = calculate(expr)
            self.assertIsInstance(result, str)
            self.assertTrue(
                result.startswith("Error"),
                f"Expected a safe error string for {expr!r}, got: {result!r}",
            )

    def test_rejects_non_numeric_names(self):
        result = calculate("some_variable + 1")
        self.assertTrue(result.startswith("Error"))


class TestWebSearch(unittest.TestCase):
    @patch("aria_core.tools_utils.requests.get")
    def test_returns_abstract_text_when_available(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "AbstractText": "Python is a programming language.",
            "AbstractSource": "Wikipedia",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = web_search("what is python")

        self.assertIn("Python is a programming language.", result)
        self.assertIn("Wikipedia", result)

    @patch("aria_core.tools_utils.requests.get")
    def test_falls_back_to_related_topics(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "AbstractText": "",
            "Answer": "",
            "RelatedTopics": [
                {"Text": "Topic one snippet"},
                {"Text": "Topic two snippet"},
            ],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = web_search("some query")

        self.assertIn("Topic one snippet", result)
        self.assertIn("Topic two snippet", result)

    @patch("aria_core.tools_utils.requests.get")
    def test_no_results_returns_explanatory_message_not_empty_string(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"AbstractText": "", "Answer": "", "RelatedTopics": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = web_search("something very obscure")

        self.assertTrue(len(result) > 0)
        self.assertIn("No quick answer", result)

    @patch("aria_core.tools_utils.requests.get")
    def test_network_failure_returns_error_string_not_exception(self, mock_get):
        mock_get.side_effect = Exception("connection timed out")

        result = web_search("anything")

        self.assertTrue(result.startswith("Error"))


if __name__ == "__main__":
    unittest.main()
