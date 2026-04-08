"""
Task 2 — Medium: Email Triage Pipeline

Objective: For each of the 15 emails, perform the full triage pipeline:
  1. classify(email_id, category)
  2. prioritize(email_id, priority)   [skip for spam]
  3. route(email_id, team)

Priority levels: critical, high, medium, low
Teams: billing_team, tech_support, general_support, spam_filter

Max steps: 60
Required actions: classify, prioritize, route
"""

TASK2 = {
    "id": "task2_medium",
    "name": "Email Triage Pipeline",
    "difficulty": "medium",
    "description": (
        "You are a support operations specialist. "
        "For each of the 15 emails in the inbox you must:\n"
        "  1. Classify: assign category (billing / technical / general / spam)\n"
        "  2. Prioritize: assign priority (critical / high / medium / low)\n"
        "     — skip prioritize for spam emails\n"
        "  3. Route: assign to the correct team\n"
        "     — billing_team  → billing emails\n"
        "     — tech_support  → technical emails\n"
        "     — general_support → general emails\n"
        "     — spam_filter   → spam emails\n\n"
        "You must classify before prioritizing or routing. "
        "Process all 15 emails completely. "
        "Prioritize critical emails (low sla_hours) early."
    ),
    "max_steps": 60,
    "required_actions": ["classify", "prioritize", "route"],
    "email_count": 15,
    "action_schema": {
        "classify": {
            "description": "Assign a category to an email",
            "params": {
                "action_type": "classify",
                "email_id": "string",
                "value": "billing | technical | general | spam",
            },
        },
        "prioritize": {
            "description": "Assign priority level to a classified email",
            "params": {
                "action_type": "prioritize",
                "email_id": "string",
                "value": "critical | high | medium | low",
            },
        },
        "route": {
            "description": "Route classified email to the appropriate team",
            "params": {
                "action_type": "route",
                "email_id": "string",
                "value": "billing_team | tech_support | general_support | spam_filter",
            },
        },
    },
    "scoring": {
        "method": "weighted_pipeline",
        "weights": {
            "classify_accuracy": 0.40,
            "priority_accuracy": 0.30,
            "routing_accuracy": 0.30,
        },
    },
}
