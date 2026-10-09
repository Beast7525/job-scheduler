import unittest
from scheduler.engine import create_schedule


class PriorityDeadlineTradeoffTests(unittest.TestCase):

    def test_critical_job_is_prioritized_when_both_jobs_are_feasible(self):
        jobs = [
            {
                "id": "NORMAL",
                "runtime": 2,
                "deadline": 10,
                "required_capacity": 1,
                "priority": "normal"
            },
            {
                "id": "CRITICAL",
                "runtime": 2,
                "deadline": 10,
                "required_capacity": 1,
                "priority": "critical"
            }
        ]

        workers = [
            {"id": "W1", "capacity": 1, "online": True}
        ]

        result = create_schedule(jobs, workers)

        self.assertEqual(
            result["assignments"][0]["job_id"],
            "CRITICAL"
        )
        self.assertEqual(
            result["assignments"][1]["job_id"],
            "NORMAL"
        )

        self.assertTrue(
            all(item["deadline_met"] for item in result["assignments"])
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
