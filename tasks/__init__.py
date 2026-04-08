from tasks.task1_easy import TASK1
from tasks.task2_medium import TASK2
from tasks.task3_hard import TASK3

TASKS = {
    "task1_easy": TASK1,
    "task2_medium": TASK2,
    "task3_hard": TASK3,
}

__all__ = ["TASKS", "TASK1", "TASK2", "TASK3"]
