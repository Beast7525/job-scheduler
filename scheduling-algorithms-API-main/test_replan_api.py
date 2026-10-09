
import unittest

from scheduler_api import app


class ReplanAPITests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

        self.payload = {
            "current_time": 2,
            "jobs": [
                {
                    "id": "J1",
                    "tenant_id": "Team_A",
                    "runtime": 5,
                    "deadline": 12,
                    "required_capacity": 1,
                    "priority": "critical"
                },
                {
                    "id": "J2",
                    "tenant_id": "Team_B",
                    "runtime": 4,
                    "deadline": 12,
                    "required_capacity": 1,
                    "priority": "normal"
                },
                {
                    "id": "J3",
                    "tenant_id": "Team_A",
                    "runtime": 2,
                    "deadline": 10,
                    "required_capacity": 1,
                    "priority": "high"
                }
            ],
            "workers": [
                {"id": "W1", "capacity": 1, "online": True},
                {"id": "W2", "capacity": 1, "online": True}
            ],
            "running_jobs": [
                {
                    "job_id": "J1",
                    "tenant_id": "Team_A",
                    "worker_id": "W1",
                    "start_time": 0,
                    "finish_time": 5,
                    "deadline": 12,
                    "priority": "critical"
                }
            ]
        }

    def test_successful_replanning(self):
        response = self.client.post(
            "/replan", json=self.payload
        )

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertEqual(
            result["running_jobs"][0]["job_id"], "J1"
        )

        assignments = {
            item["job_id"]: item
            for item in result["assignments"]
        }

        self.assertEqual(
            assignments["J3"]["start_time"], 2
        )
        self.assertEqual(
            assignments["J3"]["finish_time"], 4
        )
        self.assertEqual(
            assignments["J2"]["start_time"], 4
        )
        self.assertEqual(
            assignments["J2"]["finish_time"], 8
        )

        self.assertEqual(result["unscheduled"], [])

    def test_unknown_running_job_rejected(self):
        payload = dict(self.payload)
        payload["running_jobs"] = [
            {
                "job_id": "UNKNOWN",
                "worker_id": "W1",
                "finish_time": 5
            }
        ]

        response = self.client.post("/replan", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("unknown job_id", response.get_json()["error"])

    def test_offline_worker_not_used(self):
        payload = dict(self.payload)
        payload["workers"] = [
            {"id": "W1", "capacity": 1, "online": True},
            {"id": "W2", "capacity": 1, "online": False}
        ]

        response = self.client.post("/replan", json=payload)

        self.assertEqual(response.status_code, 200)

        result = response.get_json()

        self.assertTrue(result["assignments"])

        for assignment in result["assignments"]:
            self.assertEqual(assignment["worker_id"], "W1")
            self.assertGreaterEqual(
                assignment["start_time"], 5
            )

    def test_missing_jobs_array_rejected(self):
        payload = dict(self.payload)
        payload.pop("jobs")

        response = self.client.post("/replan", json=payload)

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)