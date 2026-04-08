---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
---

# Email Triage OpenEnv

> A production-quality RL environment for the **Meta PyTorch OpenEnv Hackathon**.

---

## Why Email Triage?

Every company — from two-person startups to Fortune 500 enterprises — receives
hundreds or thousands of support emails daily. Routing them correctly, prioritising
the urgent ones before SLA breaches, and sending the right response template are
high-stakes decisions that cost real money when done poorly.

This environment captures that reality:

- **Classifying** an email as `billing` vs `technical` determines which team
  handles it, directly affecting customer satisfaction scores.
- **Prioritising** by urgency prevents SLA breaches that carry financial penalties.
- **Routing** to the wrong team causes unnecessary handoffs and delays.
- **Responding** with the wrong template erodes customer trust.

An LLM agent that can master this task is directly deployable in real support pipelines.

---

## Project Structure

```
email_triage_env/
├── env/
│   ├── __init__.py
│   ├── models.py        # Pydantic types: Email, Action, Observation
│   ├── data.py          # 20 static, realistic email records (with ground truth)
│   └── environment.py   # Core env: reset(), step(), state()
├── tasks/
│   ├── __init__.py
│   ├── task1_easy.py    # Task config: classify 10 emails
│   ├── task2_medium.py  # Task config: full pipeline, 15 emails
│   └── task3_hard.py    # Task config: SLA-compliant, 20 emails
├── graders/
│   ├── __init__.py
│   ├── base_grader.py   # Shared scoring utilities
│   ├── task1_grader.py  # Macro classification accuracy + spam archive rate
│   ├── task2_grader.py  # Weighted F1 across classify/prioritize/route
│   └── task3_grader.py  # Composite: accuracy + response quality + SLA
├── server/
│   ├── __init__.py
│   ├── __main__.py
│   └── app.py           # FastAPI server: /reset /step /state /grade /health
├── inference.py         # OpenAI-compatible agent loop (strict log format)
├── openenv.yaml         # Environment metadata
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## State Space

Each observation contains a list of `Email` objects with these agent-visible fields:

| Field        | Type    | Description                              |
|--------------|---------|------------------------------------------|
| `id`         | string  | Unique email identifier (`e001`–`e020`)  |
| `subject`    | string  | Email subject line                       |
| `body`       | string  | Full email body                          |
| `sender`     | string  | Sender address                           |
| `timestamp`  | string  | ISO-8601 send time                       |
| `sla_hours`  | int     | Hours until SLA breach (lower = urgent)  |
| `category`   | string? | Agent-assigned category (null initially) |
| `priority`   | string? | Agent-assigned priority (null initially) |
| `assigned_to`| string? | Assigned support team (null initially)   |
| `responded`  | bool    | Whether agent has responded              |
| `archived`   | bool    | Whether email has been archived          |

Ground-truth labels (`true_category`, `true_priority`, etc.) are **never** exposed
to the agent.

---

## Action Space

| `action_type` | `value` options                                                         | When to use                      |
|---------------|-------------------------------------------------------------------------|----------------------------------|
| `classify`    | `billing` \| `technical` \| `general` \| `spam`                        | Always first                     |
| `prioritize`  | `critical` \| `high` \| `medium` \| `low`                              | After classify, before route     |
| `route`       | `billing_team` \| `tech_support` \| `general_support` \| `spam_filter` | After classify                   |
| `respond`     | `billing_inquiry` \| `refund_process` \| `tech_issue_ack` \| `escalation_notice` \| `general_ack` | Only for emails requiring response |
| `archive`     | `archive`                                                               | For spam emails                  |

---

## Reward Design

### Step-level shaped rewards

| Action outcome              | Reward  |
|-----------------------------|---------|
| Correct classify            | +0.08   |
| Wrong classify              | −0.04   |
| Duplicate classify          | −0.02   |
| Correct prioritize          | +0.06   |
| Wrong prioritize            | −0.03   |
| Prioritize before classify  | −0.05   |
| Correct route               | +0.06   |
| Wrong route                 | −0.03   |
| Route before classify       | −0.05   |
| Correct respond             | +0.10   |
| Wrong template              | −0.04   |
| Respond before route        | −0.05   |
| Archive spam correctly      | +0.05   |
| Archive non-spam            | −0.06   |
| Invalid email ID            | −0.05   |

### Final score (grader)

**Task 1 (Easy)**
```
score = 0.80 × classify_accuracy + 0.20 × spam_archive_rate
```

**Task 2 (Medium)**
```
score = 0.40 × classify_accuracy
      + 0.30 × priority_accuracy
      + 0.30 × routing_accuracy
      + efficiency_bonus (up to +0.05 if done quickly and score > 0.8)
```

**Task 3 (Hard)**
```
score = 0.20 × classify_accuracy
      + 0.15 × priority_accuracy
      + 0.15 × routing_accuracy
      + 0.30 × response_accuracy   (recall + template correctness − FP penalty)
      + 0.20 × sla_compliance      (critical emails processed within 15 steps)
```

All scores are deterministic, reproducible, and in [0.0, 1.0].

---

## Baseline Scores

Measured by running `inference.py` with `meta-llama/Llama-3.3-70B-Instruct` via HuggingFace router:

| Task | Agent | Score | Steps | Notes |
|------|-------|-------|-------|-------|
| task1_easy | Llama-3.3-70B | 0.80 | 10 | Perfect classify, missed spam archive |
| task1_easy | Llama-3.3-70B (fixed prompt) | **1.00** | 12 | Perfect |
| task2_medium | Llama-3.3-70B | ~0.72 | 42 | Some priority errors |
| task3_hard | Llama-3.3-70B | ~0.65 | 59 | SLA compliance is the hard part |
| task1_easy | Random agent | ~0.27 | 25 | Baseline lower bound |
| task1_easy | Perfect oracle | 1.00 | 12 | Upper bound |

A strong model scores **≥ 0.85** on task1, **≥ 0.75** on task2, and **≥ 0.60** on task3.
Task 3 genuinely challenges frontier models due to SLA ordering constraints and template selection.

---

## Tasks

### Task 1 — Easy: Email Classification
- **Emails**: 10
- **Goal**: Classify each email into `billing`, `technical`, `general`, or `spam`
- **Required actions**: `classify` (+ `archive` for spam)
- **Max steps**: 25
- **Success threshold**: score ≥ 0.70

### Task 2 — Medium: Email Triage Pipeline
- **Emails**: 15 (includes all Task 1 emails + 5 new ones)
- **Goal**: Classify → Prioritize → Route every email
- **Required actions**: `classify`, `prioritize`, `route`
- **Max steps**: 60
- **Note**: Classifying must happen before prioritizing or routing

### Task 3 — Hard: SLA-Compliant Email Management
- **Emails**: 20 (includes all Task 2 emails + 5 critical-SLA emails)
- **Goal**: Full pipeline + respond to emails requiring a reply
- **Required actions**: `classify`, `prioritize`, `route`, `respond`
- **Max steps**: 100
- **SLA Rule**: Emails with `sla_hours ≤ 2` must be classified + routed within the first 15 steps
- **Critical emails**: e016 (payment outage), e017 (fraud), e018 (security breach)

---

## How to Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the environment server

```bash
python -m server
# or
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

### 3. Test the API manually

```bash
# Reset to task 1
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task1_easy"}'

# Classify email e001 as billing
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "classify", "email_id": "e001", "value": "billing"}'

# Check current state
curl http://localhost:7860/state

# Get final score
curl http://localhost:7860/grade
```

### 4. Run the LLM inference agent

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o"
export HF_TOKEN="sk-..."
export TASK_ID="task1_easy"

python inference.py
# or run a specific task:
python inference.py task3_hard
```

Expected output:
```
[START] task=task1_easy env=email_triage model=gpt-4o
[STEP] step=1 action=classify_e001_billing reward=0.08 done=false error=null
[STEP] step=2 action=classify_e002_technical reward=0.08 done=false error=null
...
[END] success=true steps=12 score=0.9600 rewards=0.08,0.08,...
```

---

## Docker

### Build and run

```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

### With environment variables for inference

```bash
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o" \
  -e HF_TOKEN="sk-..." \
  email-triage-env
```

---

## Deploy to HuggingFace Spaces

1. Create a new Space with **Docker** SDK.
2. Push this repository.
3. Set these Secrets in the Space settings:
   - `HF_TOKEN` — your API key
   - `API_BASE_URL` — model endpoint
   - `MODEL_NAME` — model name
4. The Space exposes the environment server on port 7860 (HF default —
   matches the local default in `inference.py`, no override required).

---

## Tests

```bash
python -m unittest tests.test_environment -v
```

11 smoke tests cover the OpenEnv contract (reset/step/state), reward shaping
(correct vs ordering-violation vs invalid-id), and grader properties
(determinism, output range, perfect-run upper bound).

---

## OpenEnv Validation

```bash
openenv validate --env email_triage --server http://localhost:7860
```

The server passes validation by:
- Responding to `POST /reset` with observation + task metadata
- Responding to `POST /step` with `{observation, reward, done, info}`
- Responding to `GET /state` with full environment state
- Keeping reward in the defined range
- Being deterministic across identical trajectories

---

## License

MIT
