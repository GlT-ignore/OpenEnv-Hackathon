"""
Static, deterministic email datasets for all three tasks.
Ground-truth labels are embedded here; the environment strips them
from agent-visible observations.
"""

from __future__ import annotations

from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# TASK 1 — Easy: 10 emails, classify only
# ---------------------------------------------------------------------------

TASK1_EMAILS: List[Dict[str, Any]] = [
    {
        "id": "e001",
        "subject": "Invoice #4521 - Double charge on my account",
        "body": (
            "Hi Support, I noticed my credit card was charged twice for invoice #4521 "
            "dated January 10. The amount of $89.99 appears twice on my statement. "
            "Please investigate and process a refund for the duplicate charge."
        ),
        "sender": "alice.morgan@example.com",
        "timestamp": "2024-01-15T08:05:00Z",
        "sla_hours": 24,
        "true_category": "billing",
        "true_priority": "high",
        "true_team": "billing_team",
        "requires_response": False,
    },
    {
        "id": "e002",
        "subject": "App crashes on startup after latest update",
        "body": (
            "Since updating to version 4.2.1 the application crashes immediately on "
            "launch. I see an error: 'NullPointerException in MainActivity'. "
            "Device: Samsung Galaxy S22, Android 13. Steps to reproduce: open app → crash."
        ),
        "sender": "bob.chen@example.com",
        "timestamp": "2024-01-15T08:20:00Z",
        "sla_hours": 8,
        "true_category": "technical",
        "true_priority": "critical",
        "true_team": "tech_support",
        "requires_response": False,
    },
    {
        "id": "e003",
        "subject": "You've WON $1,000,000 — CLAIM NOW!!!",
        "body": (
            "CONGRATULATIONS! You have been selected as our lucky winner! "
            "Send your bank details immediately to claim your prize. "
            "Act now before it expires! Click here: http://scam-prize.xyz/claim"
        ),
        "sender": "noreply@scam-prize.xyz",
        "timestamp": "2024-01-15T08:30:00Z",
        "sla_hours": 999,
        "true_category": "spam",
        "true_priority": "low",
        "true_team": "spam_filter",
        "requires_response": False,
    },
    {
        "id": "e004",
        "subject": "Question about your refund policy",
        "body": (
            "Hello, I recently purchased your software and I am not fully satisfied. "
            "I would like to know more about your 30-day refund policy and how "
            "to initiate the process. Thank you."
        ),
        "sender": "carol.james@example.com",
        "timestamp": "2024-01-15T08:45:00Z",
        "sla_hours": 48,
        "true_category": "billing",
        "true_priority": "medium",
        "true_team": "billing_team",
        "requires_response": False,
    },
    {
        "id": "e005",
        "subject": "Cannot connect to VPN — urgent",
        "body": (
            "I have been unable to connect to the company VPN since 6 AM today. "
            "Error message: 'Authentication failed — certificate expired'. "
            "I cannot access any work systems remotely. This is blocking my entire team."
        ),
        "sender": "dave.wilson@enterprise.com",
        "timestamp": "2024-01-15T09:10:00Z",
        "sla_hours": 4,
        "true_category": "technical",
        "true_priority": "critical",
        "true_team": "tech_support",
        "requires_response": False,
    },
    {
        "id": "e006",
        "subject": "How do I change my display name?",
        "body": (
            "Hi there, I was wondering if there is a way to change the display name "
            "shown on my profile. I searched the FAQ but could not find a clear answer. "
            "Any help would be appreciated!"
        ),
        "sender": "eve.davis@example.com",
        "timestamp": "2024-01-15T09:25:00Z",
        "sla_hours": 72,
        "true_category": "general",
        "true_priority": "low",
        "true_team": "general_support",
        "requires_response": False,
    },
    {
        "id": "e007",
        "subject": "FREE Viagr@ — Best prices online!!!",
        "body": (
            "Get the best deals on ph@rmaceuticals online. No prescription needed. "
            "Worldwide shipping. Guaranteed lowest price. Order now at http://pills-cheap.ru"
        ),
        "sender": "deals@pills-cheap.ru",
        "timestamp": "2024-01-15T09:40:00Z",
        "sla_hours": 999,
        "true_category": "spam",
        "true_priority": "low",
        "true_team": "spam_filter",
        "requires_response": False,
    },
    {
        "id": "e008",
        "subject": "Subscription renewal price increase",
        "body": (
            "I just received my renewal invoice and noticed the price increased from "
            "$49/month to $69/month without prior notice. I would like to understand "
            "the reason for this 40% increase and whether there are any discounts available."
        ),
        "sender": "frank.liu@business.com",
        "timestamp": "2024-01-15T10:00:00Z",
        "sla_hours": 24,
        "true_category": "billing",
        "true_priority": "medium",
        "true_team": "billing_team",
        "requires_response": False,
    },
    {
        "id": "e009",
        "subject": "Data export feature not working",
        "body": (
            "The CSV export button on the Reports page throws an error: "
            "'Export failed: timeout after 30s'. This has been happening for 2 days. "
            "I urgently need to export data for a board presentation tomorrow."
        ),
        "sender": "grace.park@company.org",
        "timestamp": "2024-01-15T10:15:00Z",
        "sla_hours": 6,
        "true_category": "technical",
        "true_priority": "high",
        "true_team": "tech_support",
        "requires_response": False,
    },
    {
        "id": "e010",
        "subject": "Feedback on your onboarding documentation",
        "body": (
            "I recently went through your onboarding guide and wanted to share some feedback. "
            "Overall it is well written, but step 4 of the integration setup is unclear. "
            "The screenshot appears to be from an older UI version. "
            "Hope this helps your team improve the docs!"
        ),
        "sender": "henry.nguyen@startup.io",
        "timestamp": "2024-01-15T10:30:00Z",
        "sla_hours": 120,
        "true_category": "general",
        "true_priority": "low",
        "true_team": "general_support",
        "requires_response": False,
    },
]


# ---------------------------------------------------------------------------
# TASK 2 — Medium: 15 emails, classify + prioritize + route
# ---------------------------------------------------------------------------

TASK2_EMAILS: List[Dict[str, Any]] = TASK1_EMAILS + [
    {
        "id": "e011",
        "subject": "URGENT: Production database down",
        "body": (
            "Our production PostgreSQL database has been unresponsive for the past 20 minutes. "
            "All customer-facing services are affected. Revenue loss is ongoing. "
            "Error: 'max_connections exceeded — connection pool exhausted'. "
            "This is a P0 incident. Please escalate immediately."
        ),
        "sender": "oncall@bigcorp.com",
        "timestamp": "2024-01-15T10:45:00Z",
        "sla_hours": 1,
        "true_category": "technical",
        "true_priority": "critical",
        "true_team": "tech_support",
        "requires_response": False,
    },
    {
        "id": "e012",
        "subject": "Discount code not applying at checkout",
        "body": (
            "I have a promo code SAVE20 that was given to me by your sales team. "
            "When I try to apply it at checkout it says 'Invalid or expired code'. "
            "I confirmed with sales that it should be valid until January 31st. "
            "Please help me use this code for my purchase."
        ),
        "sender": "iris.schmidt@example.com",
        "timestamp": "2024-01-15T11:00:00Z",
        "sla_hours": 12,
        "true_category": "billing",
        "true_priority": "medium",
        "true_team": "billing_team",
        "requires_response": False,
    },
    {
        "id": "e013",
        "subject": "Claim your free iPhone 15 — Limited offer!",
        "body": (
            "Dear Customer, You have been randomly selected! Complete our 2-minute survey "
            "to receive your FREE iPhone 15 Pro. Only 7 left! Act NOW: http://freephone-scam.net"
        ),
        "sender": "offers@freephone-scam.net",
        "timestamp": "2024-01-15T11:15:00Z",
        "sla_hours": 999,
        "true_category": "spam",
        "true_priority": "low",
        "true_team": "spam_filter",
        "requires_response": False,
    },
    {
        "id": "e014",
        "subject": "How do I add team members to my account?",
        "body": (
            "I recently upgraded to the Business plan and I want to invite my colleagues. "
            "I found the 'Team' section but the invite button seems greyed out. "
            "Am I missing a step? Using Chrome on Windows 11."
        ),
        "sender": "jake.ford@mybusiness.com",
        "timestamp": "2024-01-15T11:30:00Z",
        "sla_hours": 48,
        "true_category": "general",
        "true_priority": "medium",
        "true_team": "general_support",
        "requires_response": False,
    },
    {
        "id": "e015",
        "subject": "API rate limit causing service degradation",
        "body": (
            "We are hitting your API rate limits (429 errors) during peak traffic hours "
            "between 9 AM and 11 AM UTC. Our current plan allows 1000 req/min but we need "
            "at least 5000. This is impacting our SLA with our own customers. "
            "Please advise on upgrading our API quota urgently."
        ),
        "sender": "api-team@techfirm.io",
        "timestamp": "2024-01-15T11:45:00Z",
        "sla_hours": 4,
        "true_category": "technical",
        "true_priority": "high",
        "true_team": "tech_support",
        "requires_response": False,
    },
]


# ---------------------------------------------------------------------------
# TASK 3 — Hard: 20 emails, full pipeline + ordering + respond to critical
# ---------------------------------------------------------------------------

TASK3_EMAILS: List[Dict[str, Any]] = TASK2_EMAILS + [
    {
        "id": "e016",
        "subject": "Payment processor integration broken — live site down",
        "body": (
            "Our Stripe webhook integration stopped working at 2 AM. All payment attempts "
            "are failing with 'webhook signature verification failed'. "
            "We have been unable to process any transactions for 4 hours. "
            "We are losing thousands of dollars per hour. Please help IMMEDIATELY."
        ),
        "sender": "cto@ecommerce-startup.com",
        "timestamp": "2024-01-15T06:15:00Z",
        "sla_hours": 1,
        "true_category": "technical",
        "true_priority": "critical",
        "true_team": "tech_support",
        "requires_response": True,
    },
    {
        "id": "e017",
        "subject": "Unauthorized charges on enterprise account",
        "body": (
            "We detected $4,200 in charges on our enterprise account that we did not authorize. "
            "These appear to be from January 12-14 for 'API overage fees'. "
            "We have never exceeded our quota before. This may be a billing error or fraud. "
            "Please freeze the account and investigate immediately."
        ),
        "sender": "finance@bigenterprise.com",
        "timestamp": "2024-01-15T06:30:00Z",
        "sla_hours": 2,
        "true_category": "billing",
        "true_priority": "critical",
        "true_team": "billing_team",
        "requires_response": True,
    },
    {
        "id": "e018",
        "subject": "Security breach — customer data possibly exposed",
        "body": (
            "We received an alert that our customer database may have been accessed without "
            "authorization. The access logs show an unknown IP address at 3:47 AM. "
            "We are unsure of the extent of the breach. We need your security team to "
            "audit our account and help us assess and contain the situation."
        ),
        "sender": "security@midsize-corp.com",
        "timestamp": "2024-01-15T07:00:00Z",
        "sla_hours": 1,
        "true_category": "technical",
        "true_priority": "critical",
        "true_team": "tech_support",
        "requires_response": True,
    },
    {
        "id": "e019",
        "subject": "Best mortgage rates — apply today",
        "body": (
            "Get the best mortgage rates in 2024! Apply online in minutes. "
            "No credit check required. Rates as low as 2.9%. "
            "Click here: http://mortgage-spam.biz"
        ),
        "sender": "offers@mortgage-spam.biz",
        "timestamp": "2024-01-15T07:30:00Z",
        "sla_hours": 999,
        "true_category": "spam",
        "true_priority": "low",
        "true_team": "spam_filter",
        "requires_response": False,
    },
    {
        "id": "e020",
        "subject": "Requesting account consolidation across subsidiaries",
        "body": (
            "We have 5 separate accounts under different subsidiary names and we would "
            "like to consolidate them under a single parent account for unified billing "
            "and reporting. Could you advise on the process and any pricing implications?"
        ),
        "sender": "operations@holdingco.com",
        "timestamp": "2024-01-15T07:45:00Z",
        "sla_hours": 48,
        "true_category": "billing",
        "true_priority": "medium",
        "true_team": "billing_team",
        "requires_response": False,
    },
]
