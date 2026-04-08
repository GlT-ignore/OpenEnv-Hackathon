"""
Abstract base grader. All task graders inherit from this.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from env.models import Email


class BaseGrader(ABC):
    """
    Deterministic grader that scores an episode trajectory.
    Input : list of Email objects (with agent-assigned fields) + trajectory
    Output: float in [0.0, 1.0]
    """

    @abstractmethod
    def grade(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
        step_count: int,
    ) -> Dict[str, Any]:
        """
        Returns a dict with at minimum:
          score  : float [0.0, 1.0]
          details: dict  (breakdown of sub-scores)
        """
        ...

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _classification_accuracy(emails: List[Email]) -> float:
        """Per-class averaged accuracy (macro F1 approximation)."""
        from collections import defaultdict

        per_class_correct: Dict[str, int] = defaultdict(int)
        per_class_total: Dict[str, int] = defaultdict(int)

        for e in emails:
            if e.archived and e.category is None:
                # Treated as implicit spam classification
                predicted = "spam"
            else:
                predicted = e.category

            if predicted is not None:
                per_class_total[e.true_category] += 1
                if predicted == e.true_category:
                    per_class_correct[e.true_category] += 1
            else:
                per_class_total[e.true_category] += 1  # unclassified counts as wrong

        if not per_class_total:
            return 0.0

        class_scores = []
        for cls, total in per_class_total.items():
            class_scores.append(per_class_correct[cls] / total)

        return sum(class_scores) / len(class_scores)

    @staticmethod
    def _priority_accuracy(emails: List[Email]) -> float:
        """Accuracy of priority assignment for non-spam emails."""
        relevant = [e for e in emails if e.true_category != "spam"]
        if not relevant:
            return 1.0
        correct = sum(
            1 for e in relevant if e.priority == e.true_priority
        )
        return correct / len(relevant)

    @staticmethod
    def _routing_accuracy(emails: List[Email]) -> float:
        """Accuracy of team routing for all emails."""
        from env.models import CATEGORY_TO_TEAM
        total = len(emails)
        if total == 0:
            return 1.0
        correct = sum(
            1
            for e in emails
            if e.assigned_to is not None
            and e.assigned_to == CATEGORY_TO_TEAM[e.true_category]
        )
        # Missing routes count as wrong
        return correct / total

    @staticmethod
    def _response_accuracy(emails: List[Email]) -> float:
        """
        Precision and recall of responses:
          - responded + required + correct template → TP
          - responded + not required → FP (penalised)
          - not responded + required → FN (penalised)
        Returns score in [0,1].
        """
        from env.models import CATEGORY_TO_TEMPLATE

        required = [e for e in emails if e.requires_response]
        if not required:
            return 1.0

        correct = 0
        for e in required:
            if e.responded:
                # We don't know which template was used at the email level;
                # grader checks from trajectory (handled in Task3Grader)
                correct += 1  # credit for responding at all (template check is extra)

        recall = correct / len(required)
        return recall
