import unittest
from scheduler_api import app


class SchedulerAPITests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_valid_schedule(self):
        payload = {
            "policy": "proposed",
            "current_time": 0,
            "jobs": [
                {
                    "id": "J101",
                    "runtime": 3,
                    "deadline": 8,
                    "required_capacity": 1,
                    "priority": "critical",
                    "tenant_id": "Team_A"
                }
            ],
            "workers": [
                {
                    "id": "W1",
                    "capacity": 1,
                    "online": True
                }
            ]
        }

        response = self.client.post("/schedule", json=payload)

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(len(result["assignments"]), 1)
        self.assertEqual(result["assignments"][0]["job_id"], "J101")
        self.assertEqual(
            result["metrics"]["deadline_compliance_percent"], 100.0
        )

    def test_negative_runtime_rejected(self):
        payload = {
            "jobs": [
                {
                    "id": "BAD1",
                    "runtime": -5,
                    "deadline": 10,
                    "required_capacity": 1
                }
            ],
            "workers": [
                {"id": "W1", "capacity": 1}
            ]
        }

        response = self.client.post("/schedule", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("runtime must be greater than zero",
                      response.get_json()["error"])

    def test_invalid_policy_rejected(self):
        payload = {
            "policy": "unknown",
            "jobs": [],
            "workers": []
        }

        response = self.client.post("/schedule", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Invalid policy")


if __name__ == "__main__":
    unittest.main(verbosity=2)