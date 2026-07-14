from django.test import TestCase

from analyzer.services.ai_fix import summarize_ai_changes, summarize_ai_suggestions


class AIFixProcessingTests(TestCase):
    def test_summarize_ai_changes_ignores_whitespace_issues_and_groups_duplicates(self):
        changes = [
            {"issue": "Missing docstring", "line": 3, "old": "x = 1", "new": '"""Doc."""\nx = 1"', "reason": "Add docs"},
            {"issue": "Missing docstring", "line": 8, "old": "y = 2", "new": '"""Doc."""\ny = 2"', "reason": "Add docs"},
            {"issue": "Trailing whitespace", "line": 10, "old": "print('hi') ", "new": "print('hi')", "reason": "Trim spaces"},
        ]

        result = summarize_ai_changes(changes)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["issue"], "Missing docstring")
        self.assertEqual(result[0]["count"], 2)
        self.assertEqual(result[0]["lines"], [3, 8])

    def test_summarize_ai_suggestions_filters_whitespace_and_groups_duplicates(self):
        suggestions = [
            "Use a helper function.",
            "Use a helper function.",
            "Remove trailing whitespace.",
            "Add type hints.",
        ]

        result = summarize_ai_suggestions(suggestions)

        self.assertEqual(result, ["Use a helper function. (2 times)", "Add type hints."])
