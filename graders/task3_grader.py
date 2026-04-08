"""
Grader for Task 3 — SLA-Compliant Full Email Management.

Score = 0.20 * classify_accuracy
      + 0.15 * priority_accuracy
      + 0.15 * routing_accuracy
      + 0.30 * response_accuracy   (correct template + responds to right emails)
      + 0.20 * sla_compliance      (critical emails fully processed within first 15 steps)
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from env.models import Email, CATEGORY_TO_TEMPLATE
from graders.base_grader import BaseGrader


SLA_CRITICAL_HOURS = 2
SLA_WINDOW_STEPS = 15


class Task3Grader(BaseGrader):
    def grade(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
        step_count: int,
    ) -> Dict[str, Any]:
        classify_acc = self._classification_accuracy(emails)
        priority_acc = self._priority_accuracy(emails)
        routing_acc = self._routing_accuracy(emails)
        response_acc = self._detailed_response_accuracy(emails, trajectory)
        sla_score = self._sla_compliance(emails, trajectory)

        raw_score = (
            0.20 * classify_acc
            + 0.15 * priority_acc
            + 0.15 * routing_acc
            + 0.30 * response_acc
            + 0.20 * sla_score
        )
        score = self._finalize_score(raw_score)

        return {
            "score": score,
            "details": {
                "classify_accuracy": round(classify_acc, 4),
                "priority_accuracy": round(priority_acc, 4),
                "routing_accuracy": round(routing_acc, 4),
                "response_accuracy": round(response_acc, 4),
                "sla_compliance": round(sla_score, 4),
                "weights": {
                    "classify_accuracy": 0.20,
                    "priority_accuracy": 0.15,
                    "routing_accuracy": 0.15,
                    "response_accuracy": 0.30,
                    "sla_compliance": 0.20,
                },
                "step_count": step_count,
            },
        }

    # ------------------------------------------------------------------
    # Task-3-specific scoring
    # ------------------------------------------------------------------

    def _detailed_response_accuracy(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
    ) -> float:
        """
        Two-part score:
          - Recall: did the agent respond to all emails requiring a response?
          - Template precision: was the correct template used?
        """
        required = [e for e in emails if e.requires_response]
        if not required:
            return 1.0

        # Build map: email_id → template used (from trajectory)
        template_used: Dict[str, str] = {}
        for step in trajectory:
            action = step.get("action", {})
            if action.get("action_type") == "respond":
                template_used[action["email_id"]] = action.get("value", "")

        recall_score = 0.0
        template_score = 0.0

        for e in required:
            if e.responded:
                recall_score += 1.0
                tmpl = template_used.get(e.id, "")
                valid_templates = CATEGORY_TO_TEMPLATE.get(e.true_category, set())
                if tmpl in valid_templates:
                    template_score += 1.0

        n = len(required)
        recall = recall_score / n
        template_prec = template_score / n if recall_score > 0 else 0.0

        # False positive penalty: responded to emails that don't need response
        not_required = [e for e in emails if not e.requires_response and e.responded]
        fp_penalty = 0.10 * len(not_required)

        combined = 0.6 * recall + 0.4 * template_prec - fp_penalty
        return max(0.0, min(1.0, combined))

    def _sla_compliance(
        self,
        emails: List[Email],
        trajectory: List[Dict[str, Any]],
    ) -> float:
        """
        Critical emails (sla_hours <= SLA_CRITICAL_HOURS) should be FULLY
        PROCESSED (classified + routed) within the first SLA_WINDOW_STEPS steps.

        Score = fraction of critical emails fully processed within SLA window.
        """
        critical_emails = [
            e for e in emails if e.sla_hours <= SLA_CRITICAL_HOURS
        ]
        if not critical_emails:
            return 1.0

        # Build per-email action step index from trajectory
        classified_at: Dict[str, int] = {}
        routed_at: Dict[str, int] = {}

        for step in trajectory:
            action = step.get("action", {})
            s = step.get("step", 999)
            eid = action.get("email_id", "")
            if action.get("action_type") == "classify" and step.get("error") is None:
                if eid not in classified_at:
                    classified_at[eid] = s
            if action.get("action_type") == "route" and step.get("error") is None:
                if eid not in routed_at:
                    routed_at[eid] = s

        compliant = 0
        for e in critical_emails:
            c_step = classified_at.get(e.id, 999)
            r_step = routed_at.get(e.id, 999)
            if c_step <= SLA_WINDOW_STEPS and r_step <= SLA_WINDOW_STEPS:
                compliant += 1

        return compliant / len(critical_emails)
