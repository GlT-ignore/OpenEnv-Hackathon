"""
Task 1 — Easy: Email Classification Only

Objective: Classify all 10 emails into the correct category.
Valid categories: billing, technical, general, spam

The agent must issue classify(email_id, category) for every email.
Spam emails should also be archived.

Max steps: 25
Required actions: classify
"""

TASK1 = {
    "id": "task1_easy",
    "name": "Email Classification",
    "difficulty": "easy",
    "description": (
        "You are a support inbox classifier. "
        "Your job is to classify each email into exactly one of these categories: "
        "'billing', 'technical', 'general', or 'spam'. "
        "Use the classify action for each email. "
        "After classifying spam emails you should also archive them. "
        "Categories:\n"
        "  billing   — payment issues, invoices, refunds, pricing\n"
        "  technical — bugs, crashes, connectivity, API errors\n"
        "  general   — how-to questions, feature requests, feedback\n"
        "  spam      — unsolicited promotional or phishing email\n"
        "Complete all 10 emails as accurately as possible."
    ),
    "max_steps": 25,
    "required_actions": ["classify"],
    "email_count": 10,
    "action_schema": {
        "classify": {
            "description": "Assign a category to an email",
            "params": {
                "action_type": "classify",
                "email_id": "string — email id (e.g. 'e001')",
                "value": "one of: billing | technical | general | spam",
            },
        },
        "archive": {
            "description": "Archive a spam email after classifying it",
            "params": {
                "action_type": "archive",
                "email_id": "string",
                "value": "archive",
            },
        },
    },
    "scoring": {
        "method": "weighted_f1",
        "weights": {
            "classify_accuracy": 0.80,
            "spam_archived": 0.20,
        },
    },
}
