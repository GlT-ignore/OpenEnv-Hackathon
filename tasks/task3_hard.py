"""
Task 3 — Hard: SLA-Compliant Full Email Management

Objective: For all 20 emails, execute the complete triage pipeline AND:
  - Respond to emails marked as requiring response (using the correct template)
  - Prioritize critical emails (sla_hours <= 2) BEFORE non-critical ones
  - Archive spam correctly

SLA ordering: emails with sla_hours <= 2 must be FULLY PROCESSED within
the first 15 steps of the episode. Violation incurs a grader penalty.

Response templates:
  billing_inquiry   — for billing questions
  refund_process    — for refund/charge disputes
  tech_issue_ack    — for technical issues
  escalation_notice — for critical technical issues
  general_ack       — for general inquiries

Max steps: 100
Required actions: classify, prioritize, route, respond
"""

TASK3 = {
    "id": "task3_hard",
    "name": "SLA-Compliant Email Management",
    "difficulty": "hard",
    "description": (
        "You are a senior support operations manager. "
        "You must manage all 20 emails with full SLA compliance:\n\n"
        "PIPELINE (for each email):\n"
        "  1. classify   → billing | technical | general | spam\n"
        "  2. prioritize → critical | high | medium | low\n"
        "  3. route      → billing_team | tech_support | general_support | spam_filter\n"
        "  4. respond    → ONLY for emails that require a response (check body carefully)\n"
        "     Templates: billing_inquiry | refund_process | tech_issue_ack | "
        "escalation_notice | general_ack\n\n"
        "SLA RULES (CRITICAL):\n"
        "  - Emails with sla_hours <= 2 MUST be fully processed in your first 15 steps\n"
        "  - critical priority emails must be routed before medium/low priority emails\n"
        "  - Do NOT respond to emails that do not require a response\n\n"
        "RESPONSE TEMPLATE GUIDE:\n"
        "  billing_inquiry    → billing questions/inquiries\n"
        "  refund_process     → unauthorized charges, refund requests\n"
        "  tech_issue_ack     → general technical problems\n"
        "  escalation_notice  → critical technical outages/breaches\n"
        "  general_ack        → general questions\n\n"
        "Score is based on: accuracy (50%) + SLA compliance (20%) + "
        "response quality (30%)."
    ),
    "max_steps": 100,
    "required_actions": ["classify", "prioritize", "route", "respond"],
    "email_count": 20,
    "sla_critical_hours": 2,
    "sla_window_steps": 15,
    "action_schema": {
        "classify": {
            "description": "Assign category",
            "params": {
                "action_type": "classify",
                "email_id": "string",
                "value": "billing | technical | general | spam",
            },
        },
        "prioritize": {
            "description": "Assign priority",
            "params": {
                "action_type": "prioritize",
                "email_id": "string",
                "value": "critical | high | medium | low",
            },
        },
        "route": {
            "description": "Route to team",
            "params": {
                "action_type": "route",
                "email_id": "string",
                "value": "billing_team | tech_support | general_support | spam_filter",
            },
        },
        "respond": {
            "description": "Send response template to email requiring a reply",
            "params": {
                "action_type": "respond",
                "email_id": "string",
                "value": (
                    "billing_inquiry | refund_process | tech_issue_ack | "
                    "escalation_notice | general_ack"
                ),
            },
        },
        "archive": {
            "description": "Archive spam email",
            "params": {
                "action_type": "archive",
                "email_id": "string",
                "value": "archive",
            },
        },
    },
    "scoring": {
        "method": "sla_weighted_composite",
        "weights": {
            "classify_accuracy": 0.20,
            "priority_accuracy": 0.15,
            "routing_accuracy": 0.15,
            "response_accuracy": 0.30,
            "sla_compliance": 0.20,
        },
    },
}
