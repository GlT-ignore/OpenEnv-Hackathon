"""
Smoke tests for the Email Triage environment.

Run with:
    python -m pytest tests/ -v
or:
    python -m unittest tests.test_environment
"""

from __future__ import annotations

import unittest

from env.environment import EmailTriageEnvironment
from tasks import TASKS
from graders import GRADERS


class TestEnvironmentBasics(unittest.TestCase):
    """Verify the OpenEnv contract: reset, step, state."""

    def test_three_tasks_registered(self):
        self.assertEqual(set(TASKS.keys()), {"task1_easy", "task2_medium", "task3_hard"})

    def test_three_graders_registered(self):
        self.assertEqual(set(GRADERS.keys()), {"task1_easy", "task2_medium", "task3_hard"})

    def test_reset_produces_clean_state(self):
        env = EmailTriageEnvironment()
        result = env.reset("task1_easy")
        self.assertIn("observation", result)
        self.assertIn("task_id", result)
        self.assertEqual(result["task_id"], "task1_easy")
        self.assertEqual(env.step_count, 0)
        self.assertEqual(len(env.trajectory), 0)

    def test_reset_unknown_task_raises(self):
        env = EmailTriageEnvironment()
        with self.assertRaises(ValueError):
            env.reset("not_a_real_task")

    def test_reset_is_idempotent(self):
        """Calling reset twice should produce the same fresh state."""
        env = EmailTriageEnvironment()
        env.reset("task2_medium")
        # Take a few steps to dirty the state
        env.step({"action_type": "classify", "email_id": "e001", "value": "billing"})
        self.assertEqual(env.step_count, 1)
        # Reset should wipe everything
        env.reset("task2_medium")
        self.assertEqual(env.step_count, 0)
        self.assertEqual(len(env.trajectory), 0)


class TestStepRewards(unittest.TestCase):
    """Verify step() returns the documented reward shape."""

    def test_correct_classify_yields_positive_reward(self):
        env = EmailTriageEnvironment()
        env.reset("task1_easy")
        # e001 is a billing email in the dataset
        obs, reward, done, info = env.step(
            {"action_type": "classify", "email_id": "e001", "value": "billing"}
        )
        self.assertGreater(reward, 0)
        self.assertFalse(done)
        self.assertEqual(info.get("classified_as"), "billing")

    def test_route_before_classify_penalised(self):
        env = EmailTriageEnvironment()
        env.reset("task2_medium")
        _, reward, _, info = env.step(
            {"action_type": "route", "email_id": "e001", "value": "billing_team"}
        )
        self.assertLess(reward, 0)
        self.assertEqual(info.get("error"), "classify_first")

    def test_invalid_email_id_penalised(self):
        env = EmailTriageEnvironment()
        env.reset("task1_easy")
        _, reward, _, info = env.step(
            {"action_type": "classify", "email_id": "nope", "value": "billing"}
        )
        self.assertLess(reward, 0)
        self.assertIn("email_not_found", info.get("error", ""))


class TestGraders(unittest.TestCase):
    """Verify graders are deterministic and produce scores in (0, 1)."""

    def test_zero_trajectory_scores_in_open_interval(self):
        """An empty/failed run should still score strictly between 0 and 1."""
        env = EmailTriageEnvironment()
        for task_id in ["task1_easy", "task2_medium", "task3_hard"]:
            env.reset(task_id)
            grader = GRADERS[task_id]()
            result = grader.grade(env.emails, env.trajectory, env.step_count)
            score = result["score"]
            with self.subTest(task_id=task_id):
                self.assertGreater(score, 0.0, f"{task_id}: score must be > 0")
                self.assertLess(score, 1.0, f"{task_id}: score must be < 1")

    def test_grader_is_deterministic(self):
        """Same trajectory must produce the same score."""
        env = EmailTriageEnvironment()
        env.reset("task1_easy")
        # Classify all 10 task1 emails correctly using their true_category
        for email in env.emails:
            env.step({
                "action_type": "classify",
                "email_id": email.id,
                "value": email.true_category,
            })

        grader = GRADERS["task1_easy"]()
        result_a = grader.grade(env.emails, env.trajectory, env.step_count)
        result_b = grader.grade(env.emails, env.trajectory, env.step_count)
        self.assertEqual(result_a["score"], result_b["score"])

    def test_perfect_run_scores_near_top_of_interval(self):
        """A perfect classification on task1 should score close to 0.999."""
        env = EmailTriageEnvironment()
        env.reset("task1_easy")
        # Perfect: classify each email with its true category, archive spam
        for email in env.emails:
            env.step({
                "action_type": "classify",
                "email_id": email.id,
                "value": email.true_category,
            })
            if email.true_category == "spam":
                env.step({
                    "action_type": "archive",
                    "email_id": email.id,
                    "value": "archive",
                })

        grader = GRADERS["task1_easy"]()
        result = grader.grade(env.emails, env.trajectory, env.step_count)
        # Reshape: 0.001 + 0.998 * 1.0 = 0.999
        self.assertGreaterEqual(result["score"], 0.99)
        self.assertLess(result["score"], 1.0)


if __name__ == "__main__":
    unittest.main()
