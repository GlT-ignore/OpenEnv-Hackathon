"""
Core Email Triage Environment.

Implements the OpenEnv contract:
  reset(task_id)  → initial observation dict
  step(action)    → (observation, reward, done, info)
  state()         → full state dict
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

from env.models import (
    Action,
    Email,
    EmailObservation,
    Observation,
    VALID_CATEGORIES,
    VALID_PRIORITIES,
    VALID_TEAMS,
    VALID_TEMPLATES,
    CATEGORY_TO_TEAM,
    CATEGORY_TO_TEMPLATE,
)
from env.data import TASK1_EMAILS, TASK2_EMAILS, TASK3_EMAILS
from tasks import TASKS


# ---------------------------------------------------------------------------
# Reward constants
# ---------------------------------------------------------------------------

REWARD = {
    # classify
    "classify_correct": 0.08,
    "classify_wrong": -0.04,
    "classify_duplicate": -0.02,
    # prioritize
    "prioritize_correct": 0.06,
    "prioritize_wrong": -0.03,
    "prioritize_before_classify": -0.05,
    "prioritize_duplicate": -0.02,
    # route
    "route_correct": 0.06,
    "route_wrong": -0.03,
    "route_before_classify": -0.05,
    "route_duplicate": -0.02,
    # respond
    "respond_correct": 0.10,
    "respond_wrong_template": -0.04,
    "respond_not_required": -0.03,
    "respond_duplicate": -0.02,
    "respond_before_route": -0.05,
    # archive
    "archive_spam": 0.05,
    "archive_non_spam": -0.06,
    "archive_duplicate": -0.02,
    # generic
    "invalid_email_id": -0.05,
    "invalid_action_type": -0.05,
    "invalid_value": -0.03,
}

TASK_EMAIL_MAP = {
    "task1_easy": TASK1_EMAILS,
    "task2_medium": TASK2_EMAILS,
    "task3_hard": TASK3_EMAILS,
}


class EmailTriageEnvironment:
    """
    Stateful email triage environment.
    One instance is shared per server session (reset between tasks).
    """

    def __init__(self) -> None:
        self._emails: List[Email] = []
        self._task_id: Optional[str] = None
        self._task_config: Dict[str, Any] = {}
        self._step_count: int = 0
        self._done: bool = False
        self._cumulative_reward: float = 0.0
        self._trajectory: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_id: str) -> Dict[str, Any]:
        """Reset environment for the given task. Returns initial observation."""
        if task_id not in TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. Valid: {list(TASKS.keys())}"
            )

        raw_emails = TASK_EMAIL_MAP[task_id]
        self._emails = [Email(**e) for e in raw_emails]
        self._task_id = task_id
        self._task_config = TASKS[task_id]
        self._step_count = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._trajectory = []

        return {
            "observation": self._build_observation().model_dump(),
            "task_id": task_id,
            "task_description": self._task_config["description"],
            "action_schema": self._task_config["action_schema"],
        }

    def step(self, action: Dict[str, Any]) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Execute one action.
        Returns (observation_dict, reward, done, info).
        """
        if self._done:
            return (
                self._build_observation().model_dump(),
                0.0,
                True,
                {"error": "episode_already_done"},
            )

        # Parse and validate action
        try:
            act = Action(**action)
        except Exception as exc:
            reward = REWARD["invalid_action_type"]
            self._cumulative_reward += reward
            self._step_count += 1
            info = {"error": f"invalid_action: {exc}", "action": action}
            self._trajectory.append({"step": self._step_count, "action": action, "reward": reward, "error": str(exc)})
            done = self._check_done()
            return self._build_observation().model_dump(), reward, done, info

        reward, info = self._dispatch(act)
        self._cumulative_reward += reward
        self._step_count += 1
        self._trajectory.append({
            "step": self._step_count,
            "action": action,
            "reward": reward,
            "error": info.get("error"),
        })

        self._done = self._check_done()
        info["step"] = self._step_count
        info["cumulative_reward"] = round(self._cumulative_reward, 4)

        return self._build_observation().model_dump(), round(reward, 4), self._done, info

    def state(self) -> Dict[str, Any]:
        """Return full environment state for inspection."""
        return {
            "task_id": self._task_id,
            "step_count": self._step_count,
            "done": self._done,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "observation": self._build_observation().model_dump(),
            "trajectory": self._trajectory,
            "completion": self._completion_stats(),
        }

    # ------------------------------------------------------------------
    # Action dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, act: Action) -> Tuple[float, Dict[str, Any]]:
        email = self._find_email(act.email_id)
        if email is None:
            return REWARD["invalid_email_id"], {"error": f"email_not_found:{act.email_id}"}

        if act.action_type == "classify":
            return self._classify(email, act.value)
        elif act.action_type == "prioritize":
            return self._prioritize(email, act.value)
        elif act.action_type == "route":
            return self._route(email, act.value)
        elif act.action_type == "respond":
            return self._respond(email, act.value)
        elif act.action_type == "archive":
            return self._archive(email)
        else:
            return REWARD["invalid_action_type"], {"error": f"unknown_action_type:{act.action_type}"}

    def _classify(self, email: Email, category: str) -> Tuple[float, Dict[str, Any]]:
        if category not in VALID_CATEGORIES:
            return REWARD["invalid_value"], {"error": f"invalid_category:{category}"}
        if email.category is not None:
            return REWARD["classify_duplicate"], {"error": "already_classified", "email_id": email.id}

        email.category = category
        correct = category == email.true_category
        reward = REWARD["classify_correct"] if correct else REWARD["classify_wrong"]
        return reward, {
            "email_id": email.id,
            "classified_as": category,
            "correct": correct,
        }

    def _prioritize(self, email: Email, priority: str) -> Tuple[float, Dict[str, Any]]:
        if priority not in VALID_PRIORITIES:
            return REWARD["invalid_value"], {"error": f"invalid_priority:{priority}"}
        if email.category is None:
            return REWARD["prioritize_before_classify"], {"error": "classify_first", "email_id": email.id}
        if email.priority is not None:
            return REWARD["prioritize_duplicate"], {"error": "already_prioritized", "email_id": email.id}

        email.priority = priority
        correct = priority == email.true_priority
        reward = REWARD["prioritize_correct"] if correct else REWARD["prioritize_wrong"]
        return reward, {
            "email_id": email.id,
            "priority_set": priority,
            "correct": correct,
        }

    def _route(self, email: Email, team: str) -> Tuple[float, Dict[str, Any]]:
        if team not in VALID_TEAMS:
            return REWARD["invalid_value"], {"error": f"invalid_team:{team}"}
        if email.category is None:
            return REWARD["route_before_classify"], {"error": "classify_first", "email_id": email.id}
        if email.assigned_to is not None:
            return REWARD["route_duplicate"], {"error": "already_routed", "email_id": email.id}

        email.assigned_to = team
        correct = team == CATEGORY_TO_TEAM[email.true_category]
        reward = REWARD["route_correct"] if correct else REWARD["route_wrong"]
        return reward, {
            "email_id": email.id,
            "routed_to": team,
            "correct": correct,
        }

    def _respond(self, email: Email, template: str) -> Tuple[float, Dict[str, Any]]:
        if template not in VALID_TEMPLATES:
            return REWARD["invalid_value"], {"error": f"invalid_template:{template}"}
        if email.assigned_to is None:
            return REWARD["respond_before_route"], {"error": "route_first", "email_id": email.id}
        if email.responded:
            return REWARD["respond_duplicate"], {"error": "already_responded", "email_id": email.id}
        if not email.requires_response:
            return REWARD["respond_not_required"], {"error": "response_not_required", "email_id": email.id}

        email.responded = True
        correct_templates = CATEGORY_TO_TEMPLATE.get(email.true_category, set())
        correct = template in correct_templates
        reward = REWARD["respond_correct"] if correct else REWARD["respond_wrong_template"]
        return reward, {
            "email_id": email.id,
            "template_used": template,
            "correct": correct,
        }

    def _archive(self, email: Email) -> Tuple[float, Dict[str, Any]]:
        if email.archived:
            return REWARD["archive_duplicate"], {"error": "already_archived", "email_id": email.id}

        email.archived = True
        is_spam = email.true_category == "spam"
        reward = REWARD["archive_spam"] if is_spam else REWARD["archive_non_spam"]
        return reward, {
            "email_id": email.id,
            "was_spam": is_spam,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_email(self, email_id: str) -> Optional[Email]:
        for e in self._emails:
            if e.id == email_id:
                return e
        return None

    def _build_observation(self) -> Observation:
        visible = [
            EmailObservation(
                id=e.id,
                subject=e.subject,
                body=e.body,
                sender=e.sender,
                timestamp=e.timestamp,
                sla_hours=e.sla_hours,
                category=e.category,
                priority=e.priority,
                assigned_to=e.assigned_to,
                responded=e.responded,
                archived=e.archived,
            )
            for e in self._emails
        ]
        pending = sum(1 for e in self._emails if e.category is None and not e.archived)
        processed = sum(1 for e in self._emails if e.category is not None or e.archived)
        return Observation(
            emails=visible,
            step_count=self._step_count,
            pending_count=pending,
            processed_count=processed,
            task_id=self._task_id or "",
        )

    def _check_done(self) -> bool:
        config = self._task_config
        max_steps = config.get("max_steps", 200)

        if self._step_count >= max_steps:
            return True

        required = config.get("required_actions", [])
        for req in required:
            if req == "classify":
                if any(e.category is None and not e.archived for e in self._emails):
                    return False
            elif req == "prioritize":
                if any(
                    e.priority is None and e.category is not None and e.true_category != "spam"
                    for e in self._emails
                ):
                    return False
            elif req == "route":
                if any(
                    e.assigned_to is None and e.category is not None and not e.archived
                    for e in self._emails
                ):
                    return False
            elif req == "respond":
                if any(
                    e.requires_response and not e.responded
                    for e in self._emails
                ):
                    return False

        return True

    def _completion_stats(self) -> Dict[str, Any]:
        total = len(self._emails)
        classified = sum(1 for e in self._emails if e.category is not None)
        prioritized = sum(1 for e in self._emails if e.priority is not None)
        routed = sum(1 for e in self._emails if e.assigned_to is not None)
        responded = sum(1 for e in self._emails if e.responded)
        archived = sum(1 for e in self._emails if e.archived)
        return {
            "total": total,
            "classified": classified,
            "prioritized": prioritized,
            "routed": routed,
            "responded": responded,
            "archived": archived,
        }

    # ------------------------------------------------------------------
    # Expose trajectory for grader
    # ------------------------------------------------------------------

    @property
    def emails(self) -> List[Email]:
        return self._emails

    @property
    def trajectory(self) -> List[Dict[str, Any]]:
        return self._trajectory

    @property
    def task_id(self) -> Optional[str]:
        return self._task_id

    @property
    def step_count(self) -> int:
        return self._step_count
