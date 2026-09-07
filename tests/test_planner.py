import json
import unittest
from unittest.mock import patch

from agents.planner import planner_agent


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, content):
        self.content = content

    def invoke(self, prompt):
        return FakeResponse(self.content)


class PlannerTests(unittest.TestCase):

    def run_planner_with_mock(self, tasks, goal):

        fake_response = json.dumps({
            "tasks": tasks
        })

        with patch(
            "agents.planner.get_llm",
            return_value=FakeLLM(fake_response)
        ):

            return planner_agent(goal)

    def test_research_task(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Research the latest Bleach episode.",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": []
            }
        ]

        result = self.run_planner_with_mock(
            tasks,
            "Explain the latest Bleach episode"
        )

        self.assertEqual(len(result["tasks"]), 1)
        self.assertEqual(
            result["tasks"][0]["agent"],
            "researcher"
        )
        self.assertEqual(
            result["tasks"][0]["task_type"],
            "research"
        )

    def test_research_then_questions(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Research the latest Bleach episode.",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": []
            },
            {
                "task_id": 2,
                "description": "Create 10 questions with answers.",
                "agent": "content",
                "task_type": "questions",
                "depends_on": [1]
            }
        ]

        result = self.run_planner_with_mock(
            tasks,
            "Create 10 questions about the latest Bleach episode with answers"
        )

        self.assertEqual(len(result["tasks"]), 2)

        self.assertEqual(
            result["tasks"][0]["agent"],
            "researcher"
        )

        self.assertEqual(
            result["tasks"][1]["agent"],
            "content"
        )

        self.assertEqual(
            result["tasks"][1]["task_type"],
            "questions"
        )

        self.assertEqual(
            result["tasks"][1]["depends_on"],
            [1]
        )

    def test_coding_task(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Build a Python calculator.",
                "agent": "coder",
                "task_type": "coding",
                "depends_on": []
            }
        ]

        result = self.run_planner_with_mock(
            tasks,
            "Build a Python calculator"
        )

        self.assertEqual(len(result["tasks"]), 1)

        self.assertEqual(
            result["tasks"][0]["agent"],
            "coder"
        )

        self.assertEqual(
            result["tasks"][0]["task_type"],
            "coding"
        )

    def test_research_then_coding(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Research the recommended FastAPI REST API architecture.",
                "agent": "researcher",
                "task_type": "research",
                "depends_on": []
            },
            {
                "task_id": 2,
                "description": "Implement the FastAPI REST API.",
                "agent": "coder",
                "task_type": "coding",
                "depends_on": [1]
            }
        ]

        result = self.run_planner_with_mock(
            tasks,
            "Research the best way to build a REST API in FastAPI and then create the implementation"
        )

        self.assertEqual(len(result["tasks"]), 2)

        self.assertEqual(
            result["tasks"][0]["agent"],
            "researcher"
        )

        self.assertEqual(
            result["tasks"][1]["agent"],
            "coder"
        )

        self.assertEqual(
            result["tasks"][1]["depends_on"],
            [1]
        )

    def test_content_task(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Summarize the requested topic.",
                "agent": "content",
                "task_type": "content",
                "depends_on": []
            }
        ]

        result = self.run_planner_with_mock(
            tasks,
            "Summarize a topic"
        )

        self.assertEqual(len(result["tasks"]), 1)

        self.assertEqual(
            result["tasks"][0]["agent"],
            "content"
        )

        self.assertEqual(
            result["tasks"][0]["task_type"],
            "content"
        )

    def test_evaluator_is_not_allowed_as_planner_task(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Evaluate the result.",
                "agent": "evaluator",
                "task_type": "content",
                "depends_on": []
            }
        ]

        with self.assertRaises(ValueError):

            self.run_planner_with_mock(
                tasks,
                "Evaluate this result"
            )

    def test_finalizer_is_not_allowed_as_planner_task(self):

        tasks = [
            {
                "task_id": 1,
                "description": "Finalize the answer.",
                "agent": "finalizer",
                "task_type": "content",
                "depends_on": []
            }
        ]

        with self.assertRaises(ValueError):

            self.run_planner_with_mock(
                tasks,
                "Finalize this answer"
            )


if __name__ == "__main__":
    unittest.main()