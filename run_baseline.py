"""
run_baseline.py — Run inference.py across all 3 tasks and print a score summary.

Usage:
  python run_baseline.py

Reads same env vars as inference.py:
  API_BASE_URL, MODEL_NAME, HF_TOKEN, ENV_SERVER_URL
"""

from __future__ import annotations

import os
import sys
import subprocess
import re

TASKS = ["task1_easy", "task2_medium", "task3_hard"]
ENV_SERVER_URL = os.environ.get("ENV_SERVER_URL", "http://localhost:8000")


def run_task(task_id: str) -> dict:
    env = os.environ.copy()
    env["TASK_ID"] = task_id
    env["ENV_SERVER_URL"] = ENV_SERVER_URL

    result = subprocess.run(
        [sys.executable, "inference.py", task_id],
        capture_output=True,
        text=True,
        env=env,
        timeout=1200,  # 20 min hard limit per task
    )

    output = result.stdout
    stderr = result.stderr

    # Parse [END] line
    end_match = re.search(
        r'\[END\] success=(\w+) steps=(\d+) score=([\d.]+) rewards=([^\n]+)',
        output
    )

    if end_match:
        return {
            "task_id": task_id,
            "success": end_match.group(1) == "true",
            "steps": int(end_match.group(2)),
            "score": float(end_match.group(3)),
            "rewards": end_match.group(4),
            "stdout": output,
            "stderr": stderr,
            "error": None,
        }
    else:
        return {
            "task_id": task_id,
            "success": False,
            "steps": 0,
            "score": 0.0,
            "rewards": "",
            "stdout": output,
            "stderr": stderr,
            "error": f"No [END] line found. stderr: {stderr[:200]}",
        }


def main() -> None:
    print("=" * 60)
    print("EMAIL TRIAGE OPENENV — BASELINE EVALUATION")
    print("=" * 60)
    print(f"Model  : {os.environ.get('MODEL_NAME', 'unknown')}")
    print(f"Server : {ENV_SERVER_URL}")
    print()

    results = []
    for task_id in TASKS:
        print(f"Running {task_id}...", end=" ", flush=True)
        try:
            r = run_task(task_id)
        except subprocess.TimeoutExpired:
            r = {"task_id": task_id, "success": False, "steps": 0,
                 "score": 0.0, "rewards": "", "error": "TIMEOUT"}
        results.append(r)

        status = "✓" if r["success"] else "✗"
        print(f"{status}  score={r['score']:.4f}  steps={r['steps']}")
        if r.get("error"):
            print(f"  ERROR: {r['error']}", file=sys.stderr)

    # Summary table
    print()
    print("=" * 60)
    print(f"{'TASK':<20} {'SCORE':>8} {'STEPS':>7} {'SUCCESS':>9}")
    print("-" * 60)
    total = 0.0
    for r in results:
        total += r["score"]
        tick = "true" if r["success"] else "false"
        print(f"{r['task_id']:<20} {r['score']:>8.4f} {r['steps']:>7} {tick:>9}")
    print("-" * 60)
    print(f"{'AVERAGE':<20} {total/len(results):>8.4f}")
    print("=" * 60)

    # Exit non-zero if any task failed completely
    if any(r["score"] == 0.0 for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
