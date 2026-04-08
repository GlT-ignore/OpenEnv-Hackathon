"""
FastAPI server exposing the Email Triage environment via HTTP.

Endpoints:
  POST /reset   — start or restart a task episode
  POST /step    — execute one action
  GET  /state   — inspect current environment state
  GET  /grade   — score the current episode (final or mid-episode)
  GET  /health  — liveness probe
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from env.environment import EmailTriageEnvironment
from graders import GRADERS

app = FastAPI(
    title="Email Triage OpenEnv",
    description="A production-quality email triage RL environment.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global environment instance (stateful across requests)
env = EmailTriageEnvironment()


class ResetRequest(BaseModel):
    task_id: Optional[str] = "task1_easy"


class StepRequest(BaseModel):
    action_type: str
    email_id: str
    value: str


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "env": "email_triage"}


@app.post("/reset")
async def reset(request: Request) -> Dict[str, Any]:
    """Reset environment and return initial observation.

    Accepts an optional JSON body with `task_id`. If the body is missing,
    empty, or does not contain `task_id`, defaults to `task1_easy`.
    """
    task_id = "task1_easy"
    try:
        raw = await request.body()
        if raw:
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("task_id"):
                    task_id = data["task_id"]
            except json.JSONDecodeError:
                pass
    except Exception:
        pass

    try:
        result = env.reset(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@app.post("/step")
def step(req: StepRequest) -> Dict[str, Any]:
    """Execute one action and return (observation, reward, done, info)."""
    if env.task_id is None:
        raise HTTPException(status_code=400, detail="Call /reset first.")

    action = {
        "action_type": req.action_type,
        "email_id": req.email_id,
        "value": req.value,
    }
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state() -> Dict[str, Any]:
    """Return current environment state."""
    if env.task_id is None:
        raise HTTPException(status_code=400, detail="Call /reset first.")
    return env.state()


@app.get("/grade")
def grade() -> Dict[str, Any]:
    """Compute final grade for current episode."""
    if env.task_id is None:
        raise HTTPException(status_code=400, detail="Call /reset first.")

    grader_cls = GRADERS.get(env.task_id)
    if grader_cls is None:
        raise HTTPException(status_code=500, detail=f"No grader for task {env.task_id}")

    grader = grader_cls()
    result = grader.grade(env.emails, env.trajectory, env.step_count)
    return {
        "task_id": env.task_id,
        "score": result["score"],
        "details": result["details"],
        "done": env.state()["done"],
    }


def main() -> None:
    """Entry point for `python -m server.app` and pyproject scripts."""
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
