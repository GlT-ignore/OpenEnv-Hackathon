"""
Grader for Task 1 — Email Classification Only.

Score = 0.80 * macro_classification_accuracy + 0.20 * spam_archive_rate
"""

from __future__ import annotations

from typing import Any, Dict, List

from env.models import Email
from graders.base_grader import BaseGrader


class Task1Grader(BaseGrader):
    def grade(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
        step_count: int,
    ) -> Dict[str, Any]:
        classify_acc = self._classification_accuracy(emails)

        # Spam archive rate: how many spam emails were archived
        spam_emails = [e for e in emails if e.true_category == "spam"]
        if spam_emails:
            archived_spam = sum(1 for e in spam_emails if e.archived)
            spam_archive_rate = archived_spam / len(spam_emails)
        else:
            spam_archive_rate = 1.0

        score = 0.80 * classify_acc + 0.20 * spam_archive_rate
        score = round(min(max(score, 0.0), 1.0), 4)

        return {
            "score": score,
            "details": {
                "classify_accuracy": round(classify_acc, 4),
                "spam_archive_rate": round(spam_archive_rate, 4),
                "weights": {"classify_accuracy": 0.80, "spam_archive_rate": 0.20},
                "step_count": step_count,
            },
        }
