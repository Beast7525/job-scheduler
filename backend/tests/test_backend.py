import unittest
import json
from app import app
from db import db
from services.worker_service import reset_simulation, initialize_workers


class BackendTestSuite(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        reset_simulation()

    def test_01_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "deadline-aware-compute-optimizer")

    def test_02_worker_initialization_and_listing(self):
        response = self.client.post("/api/simulation/initialize")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("workers", data)
        self.assertEqual(len(data["workers"]), 3)

        res_list = self.client.get("/api/workers")
        self.assertEqual(res_list.status_code, 200)
        workers = res_list.get_json()["workers"]
        self.assertEqual(len(workers), 3)

    def test_03_job_submission_and_retrieval(self):
        # Valid job
        valid_job = {
            "id": "J101",
            "tenant_id": "Team-A",
            "priority": "critical",
            "runtime_estimate": 5,
            "deadline": 20,
            "required_capacity": 1
        }
        res = self.client.post("/api/jobs/", json=valid_job)
        self.assertEqual(res.status_code, 201)
        created = res.get_json()
        self.assertEqual(created["id"], "J101")
        self.assertEqual(created["status"], "queued")

        # Retrieve job by ID
        res_get = self.client.get("/api/jobs/J101")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()["id"], "J101")

        # Retrieve all jobs
        res_all = self.client.get("/api/jobs/")
        self.assertEqual(res_all.status_code, 200)
        self.assertEqual(len(res_all.get_json()["jobs"]), 1)

    def test_04_job_submission_validation(self):
        # Missing field
        invalid_job_missing = {
            "id": "J102",
            "tenant_id": "Team-B"
        }
        res = self.client.post("/api/jobs/", json=invalid_job_missing)
        self.assertEqual(res.status_code, 400)

        # Invalid priority
        invalid_prio = {
            "id": "J103",
            "tenant_id": "Team-B",
            "priority": "super-urgent",
            "runtime_estimate": 5,
            "deadline": 20,
            "required_capacity": 1
        }
        res2 = self.client.post("/api/jobs/", json=invalid_prio)
        self.assertEqual(res2.status_code, 400)

        # Duplicate ID
        duplicate_job = {
            "id": "J101",
            "tenant_id": "Team-A",
            "priority": "normal",
            "runtime_estimate": 5,
            "deadline": 20,
            "required_capacity": 1
        }
        self.client.post("/api/jobs/", json=duplicate_job)
        res_dup = self.client.post("/api/jobs/", json=duplicate_job)
        self.assertEqual(res_dup.status_code, 409)

    def test_05_scheduling_and_dispatch(self):
        # Create 2 jobs
        j1 = {"id": "J201", "tenant_id": "T1", "priority": "high", "runtime_estimate": 4, "deadline": 10, "required_capacity": 1}
        j2 = {"id": "J202", "tenant_id": "T2", "priority": "low", "runtime_estimate": 6, "deadline": 25, "required_capacity": 1}
        self.client.post("/api/jobs/", json=j1)
        self.client.post("/api/jobs/", json=j2)

        # Run scheduler plan
        res_plan = self.client.post("/api/scheduler/plan")
        self.assertEqual(res_plan.status_code, 200)
        plan = res_plan.get_json()
        self.assertIn("assignments", plan)
        self.assertGreaterEqual(len(plan["assignments"]), 1)

    def test_06_worker_failure_and_recovery(self):
        # Fail W1
        res_fail = self.client.post("/api/simulation/worker-failure", json={"worker_id": "W1"})
        self.assertEqual(res_fail.status_code, 200)
        w1 = res_fail.get_json()["worker"]
        self.assertEqual(w1["status"], "offline")

        # Recover W1
        res_rec = self.client.post("/api/simulation/worker-recovery", json={"worker_id": "W1"})
        self.assertEqual(res_rec.status_code, 200)
        w1_rec = res_rec.get_json()["worker"]
        self.assertEqual(w1_rec["status"], "online")

    def test_07_worker_capacity_update(self):
        res_cap = self.client.patch("/api/workers/W1/capacity", json={"capacity": 4})
        self.assertEqual(res_cap.status_code, 200)
        updated = res_cap.get_json()
        self.assertEqual(float(updated["capacity"]), 4.0)

    def test_08_metrics_and_reset(self):
        res_metrics = self.client.get("/api/metrics")
        self.assertEqual(res_metrics.status_code, 200)
        metrics = res_metrics.get_json()
        self.assertIn("deadline_compliance", metrics)
        self.assertIn("utilization", metrics)

        res_reset = self.client.post("/api/simulation/reset")
        self.assertEqual(res_reset.status_code, 200)
        self.assertEqual(res_reset.get_json()["status"], "reset_successful")


if __name__ == "__main__":
    unittest.main()
