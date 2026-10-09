import unittest
from scheduler.engine import create_schedule


class SchedulerRegressionTests(unittest.TestCase):

    def test_infeasible_critical_job_does_not_block_feasible_job(self):
        jobs = [
            {
                "id": "URGENT",
                "runtime": 4,
                "deadline": 3,
                "required_capacity": 1,
                "priority": "critical",
                "tenant_id": "Team_A"
            },
            {
                "id": "NORMAL",
                "runtime": 2,
                "deadline": 10,
                "required_capacity": 1,
                "priority": "normal",
                "tenant_id": "Team_B"
            }
        ]

        workers = [
            {"id": "W1", "capacity": 1, "online": True}
        ]

        result = create_schedule(jobs, workers)

        assigned_ids = {
            item["job_id"] for item in result["assignments"]
        }
        unscheduled_ids = {
            item["job_id"] for item in result["unscheduled"]
        }

        self.assertIn("NORMAL", assigned_ids)
        self.assertIn("URGENT", unscheduled_ids)

        normal = next(
            item for item in result["assignments"]
            if item["job_id"] == "NORMAL"
        )
        self.assertEqual(normal["finish_time"], 2)
        self.assertTrue(normal["deadline_met"])

        urgent = next(
            item for item in result["unscheduled"]
            if item["job_id"] == "URGENT"
        )
        self.assertEqual(urgent["reason"], "deadline_infeasible")

    def test_offline_worker_is_not_selected(self):
        jobs = [
            {
                "id": "J1",
                "runtime": 2,
                "deadline": 10,
                "required_capacity": 1
            }
        ]

        workers = [
            {"id": "W1", "capacity": 2, "online": False},
            {"id": "W2", "capacity": 1, "online": True}
        ]

        result = create_schedule(jobs, workers)

        self.assertEqual(len(result["assignments"]), 1)
        self.assertEqual(result["assignments"][0]["worker_id"], "W2")

    def test_insufficient_capacity_is_reported(self):
        jobs = [
            {
                "id": "J1",
                "runtime": 2,
                "deadline": 10,
                "required_capacity": 4
            }
        ]

        workers = [
            {"id": "W1", "capacity": 2, "online": True}
        ]

        result = create_schedule(jobs, workers)

        self.assertEqual(len(result["assignments"]), 0)
        self.assertEqual(
            result["unscheduled"][0]["reason"],
            "no_compatible_worker"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)