"""
Pydantic models for the Email Triage environment.
All types are strict and serializable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain enumerations (stored as plain strings for YAML/JSON friendliness)
# ---------------------------------------------------------------------------

VALID_CATEGORIES = {"billing", "technical", "general", "spam"}

VALID_PRIORITIES = {"critical", "high", "medium", "low"}

VALID_TEAMS = {"billing_team", "tech_support", "general_support", "spam_filter"}

VALID_TEMPLATES = {
    "billing_inquiry",     # Acknowledge billing question / request payment info
    "tech_issue_ack",      # Acknowledge technical problem, provide ticket number
    "general_ack",         # Generic acknowledgement
    "refund_process",      # Explain refund procedure
    "escalation_notice",   # Notify customer that issue is escalated
}

# Which response template is correct for each category
CATEGORY_TO_TEMPLATE = {
    "billing": {"billing_inquiry", "refund_process"},
    "technical": {"tech_issue_ack", "escalation_notice"},
    "general": {"general_ack"},
    "spam": set(),  # spam should be archived, not responded to
}

# Which team is correct for each category
CATEGORY_TO_TEAM = {
    "billing": "billing_team",
    "technical": "tech_support",
    "general": "general_support",
    "spam": "spam_filter",
}


# ---------------------------------------------------------------------------
# Email model
# ---------------------------------------------------------------------------

class Email(BaseModel):
    """A single email in the inbox. Ground-truth fields are prefixed with true_."""

    id: str
    subject: str
    body: str
    sender: str
    timestamp: str
    sla_hours: int = Field(description="Hours until SLA breach. Lower = more urgent.")

    # Mutable agent-assigned fields
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    responded: bool = False
    archived: bool = False

    # Ground truth (always present internally; stripped from agent observations)
    true_category: str
    true_priority: str
    true_team: str
    requires_response: bool


# ---------------------------------------------------------------------------
# Action model
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """
    A single agent action.

    action_type : one of "classify" | "prioritize" | "route" | "respond" | "archive"
    email_id    : target email id (e.g. "e001")
    value       : depends on action_type —
                  classify   → category name
                  prioritize → priority name
                  route      → team name
                  respond    → template name
                  archive    → (ignored, use "archive")
    """

    action_type: str
    email_id: str
    value: str


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------

class EmailObservation(BaseModel):
    """Agent-visible email state (no ground truth)."""

    id: str
    subject: str
    body: str
    sender: str
    timestamp: str
    sla_hours: int
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    responded: bool = False
    archived: bool = False


class Observation(BaseModel):
    emails: List[EmailObservation]
    step_count: int
    pending_count: int
    processed_count: int
    task_id: str


class StepResult(BaseModel):
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


class ResetResult(BaseModel):
    observation: Dict[str, Any]
    task_id: str
    task_description: str
    action_schema: Dict[str, Any]


class StateResult(BaseModel):
    state: Dict[str, Any]
    task_id: str
    step_count: int
    done: bool
    cumulative_reward: float
