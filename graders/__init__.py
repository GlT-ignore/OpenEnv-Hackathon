from graders.task1_grader import Task1Grader
from graders.task2_grader import Task2Grader
from graders.task3_grader import Task3Grader

GRADERS = {
    "task1_easy": Task1Grader,
    "task2_medium": Task2Grader,
    "task3_hard": Task3Grader,
}

__all__ = ["GRADERS", "Task1Grader", "Task2Grader", "Task3Grader"]
