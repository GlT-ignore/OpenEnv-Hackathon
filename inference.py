"""
inference.py — OpenEnv Hackathon inference script.

Reads environment variables:
  API_BASE_URL  — OpenAI-compatible API endpoint (e.g. https://api.openai.com/v1)
  MODEL_NAME    — model to query (e.g. gpt-4o)
  HF_TOKEN      — bearer token / API key

Interacts with the local environment server via HTTP.
Prints EXACTLY the required log format:

  [START] task=<task_name> env=<env_name> model=<model_name>
  [STEP]  step=<n> action=<action> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...>
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o")
HF_TOKEN: str = os.environ.get("HF_TOKEN", "")
ENV_SERVER_URL: str = os.environ.get("ENV_SERVER_URL", "http://localhost:8000")
TASK_ID: str = os.environ.get("TASK_ID", "task1_easy")
ENV_NAME: str = "email_triage"

# ---------------------------------------------------------------------------
# OpenAI-compatible client
# ---------------------------------------------------------------------------

client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

# ---------------------------------------------------------------------------
# System prompt for the LLM agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an email triage agent. Output ONE JSON action per turn. Nothing else.

VALID ACTIONS (pick one):
{"action_type": "classify",   "email_id": "e001", "value": "billing"}
{"action_type": "classify",   "email_id": "e001", "value": "technical"}
{"action_type": "classify",   "email_id": "e001", "value": "general"}
{"action_type": "classify",   "email_id": "e001", "value": "spam"}
{"action_type": "prioritize", "email_id": "e001", "value": "critical"}
{"action_type": "prioritize", "email_id": "e001", "value": "high"}
{"action_type": "prioritize", "email_id": "e001", "value": "medium"}
{"action_type": "prioritize", "email_id": "e001", "value": "low"}
{"action_type": "route",      "email_id": "e001", "value": "billing_team"}
{"action_type": "route",      "email_id": "e001", "value": "tech_support"}
{"action_type": "route",      "email_id": "e001", "value": "general_support"}
{"action_type": "route",      "email_id": "e001", "value": "spam_filter"}
{"action_type": "archive",    "email_id": "e001", "value": "archive"}

RULES:
1. Always classify an email before routing or prioritizing it.
2. IMPORTANT: Immediately after classifying an email as spam, your NEXT action must archive it:
   {"action_type": "archive", "email_id": "<same id>", "value": "archive"}
3. Do NOT add any text before or after the JSON. Output ONLY the JSON object.
"""


def build_user_prompt(observation: Dict[str, Any], task_description: str) -> str:
    emails = observation.get("emails", [])
    pending = [e for e in emails if not e.get("archived") and e.get("category") is None]
    classified_not_routed = [
        e for e in emails
        if e.get("category") is not None and e.get("assigned_to") is None and not e.get("archived")
    ]
    needs_response = [
        e for e in emails
        if e.get("assigned_to") is not None and not e.get("responded")
        and not e.get("archived")
    ]

    lines = [
        f"TASK: {task_description}",
        "",
        f"Step: {observation.get('step_count', 0)} | "
        f"Pending: {observation.get('pending_count', 0)} | "
        f"Processed: {observation.get('processed_count', 0)}",
        "",
    ]

    if pending:
        lines.append("=== UNCLASSIFIED EMAILS (classify these first) ===")
        for e in sorted(pending, key=lambda x: x.get("sla_hours", 999)):
            lines.append(
                f"[{e['id']}] SLA:{e['sla_hours']}h | FROM: {e['sender']}\n"
                f"  SUBJECT: {e['subject']}\n"
                f"  BODY: {e['body'][:200]}"
            )
        lines.append("")

    if classified_not_routed:
        lines.append("=== CLASSIFIED BUT NOT YET ROUTED ===")
        for e in classified_not_routed:
            lines.append(
                f"[{e['id']}] category={e.get('category')} priority={e.get('priority')} "
                f"assigned_to={e.get('assigned_to')}"
            )
        lines.append("")

    if needs_response:
        lines.append("=== ROUTED BUT AWAITING RESPONSE ===")
        for e in needs_response:
            lines.append(
                f"[{e['id']}] {e['subject'][:60]} (team={e.get('assigned_to')})"
            )
        lines.append("")

    lines.append("Issue ONE action JSON now:")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Environment HTTP helpers
# ---------------------------------------------------------------------------

def env_reset(task_id: str) -> Dict[str, Any]:
    resp = httpx.post(f"{ENV_SERVER_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> Dict[str, Any]:
    resp = httpx.post(
        f"{ENV_SERVER_URL}/step",
        json=action,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_grade() -> Dict[str, Any]:
    resp = httpx.get(f"{ENV_SERVER_URL}/grade", timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# LLM agent
# ---------------------------------------------------------------------------

def query_llm(messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """Call the LLM and parse a JSON action from the response."""
    import re
    content = ""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.0,
            max_tokens=128,
        )
        content = (response.choices[0].message.content or "").strip()

        # Strip markdown code fences if present
        if "```" in content:
            for part in content.split("```"):
                part = part.strip().lstrip("json").strip()
                try:
                    return json.loads(part)
                except Exception:
                    continue

        # Extract first {...} JSON object from anywhere in the response
        match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())

        return json.loads(content)
    except Exception as exc:
        err_str = str(exc)
        print(f"[WARN] LLM failed. error={exc!r} raw={content[:300]!r}", file=sys.stderr)
        # Fatal errors — no point retrying
        if any(code in err_str for code in ["402", "401", "403", "410", "429"]):
            raise RuntimeError(f"FATAL_API_ERROR: {err_str}") from exc
        return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run(task_id: str = TASK_ID) -> None:
    # Reset
    reset_data = env_reset(task_id)
    observation = reset_data["observation"]
    task_description = reset_data["task_description"]


    print(f"[START] task={task_id} env={ENV_NAME} model={MODEL_NAME}")

    rewards: List[float] = []
    step_n = 0
    done = False
    success = False

    # Conversation history for the LLM
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    while not done:
        step_n += 1

        # Build prompt
        user_content = build_user_prompt(observation, task_description)
        messages.append({"role": "user", "content": user_content})

        # Query LLM
        try:
            action = query_llm(messages)
        except RuntimeError as fatal:
            print(f"[END] success=false steps={step_n} score=0.0000 rewards={','.join(f'{r:.2f}' for r in rewards)}")
            print(f"[FATAL] {fatal}", file=sys.stderr)
            return

        if action is None:
            # Fallback: skip with a no-op that will produce an error
            action = {"action_type": "classify", "email_id": "unknown", "value": "general"}

        # Execute action
        try:
            result = env_step(action)
        except Exception as exc:
            print(
                f"[STEP] step={step_n} action={json.dumps(action)} "
                f"reward=0.00 done=false error={str(exc)}"
            )
            rewards.append(0.0)
            # Add assistant turn for history
            messages.append({"role": "assistant", "content": json.dumps(action)})
            continue

        reward = result.get("reward", 0.0)
        done = result.get("done", False)
        info = result.get("info", {})
        observation = result.get("observation", observation)
        error = info.get("error") or "null"

        rewards.append(reward)

        # Format action string for log
        action_str = (
            f"{action.get('action_type')}_{action.get('email_id')}_{action.get('value')}"
        )
        done_str = "true" if done else "false"

        print(
            f"[STEP] step={step_n} action={action_str} "
            f"reward={reward:.2f} done={done_str} error={error}"
        )

        # Add to conversation history
        messages.append({"role": "assistant", "content": json.dumps(action)})

        if done:
            break

    # Grade
    grade_result = env_grade()
    score = grade_result.get("score", 0.0)
    success = score >= 0.7

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"

    print(
        f"[END] success={success_str} steps={step_n} "
        f"score={score:.4f} rewards={rewards_str}"
    )


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else TASK_ID
    run(task)
