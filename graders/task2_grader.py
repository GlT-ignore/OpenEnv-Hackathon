"""
Grader for Task 2 — Email Triage Pipeline.

Score = 0.40 * classify_accuracy
      + 0.30 * priority_accuracy
      + 0.30 * routing_accuracy
"""

from __future__ import annotations

from typing import Any, Dict, List

from env.models import Email
from graders.base_grader import BaseGrader


class Task2Grader(BaseGrader):
    def grade(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
        step_count: int,
    ) -> Dict[str, Any]:
        classify_acc = self._classification_accuracy(emails)
        priority_acc = self._priority_accuracy(emails)
        routing_acc = self._routing_accuracy(emails)

        raw_score = (
            0.40 * classify_acc
            + 0.30 * priority_acc
            + 0.30 * routing_acc
        )

        # Efficiency bonus: if completed in fewer steps than 80% of max_steps
        max_steps = 60
        if step_count <= int(0.80 * max_steps) and raw_score > 0.8:
            efficiency_bonus = 0.05 * (1 - step_count / max_steps)
            raw_score = min(raw_score + efficiency_bonus, 1.0)

        score = self._finalize_score(raw_score)

        return {
            "score": score,
            "details": {
                "classify_accuracy": round(classify_acc, 4),
                "priority_accuracy": round(priority_acc, 4),
                "routing_accuracy": round(routing_acc, 4),
                "weights": {
                    "classify_accuracy": 0.40,
                    "priority_accuracy": 0.30,
                    "routing_accuracy": 0.30,
                },
                "step_count": step_count,
            },
        }
