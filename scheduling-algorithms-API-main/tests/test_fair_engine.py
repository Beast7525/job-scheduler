
from scheduler.fair_engine import create_fair_schedule

jobs = [
    {"id": "A1", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 20, "required_capacity": 1},
    {"id": "A2", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 25, "required_capacity": 1},
    {"id": "A3", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 2, "deadline": 30, "required_capacity": 1},
    {"id": "B1", "tenant_id": "Team_B", "priority": "normal",
     "runtime": 2, "deadline": 15, "required_capacity": 1},
    {"id": "B2", "tenant_id": "Team_B", "priority": "normal",
     "runtime": 2, "deadline": 22, "required_capacity": 1},
    {"id": "C1", "tenant_id": "Team_C", "priority": "critical",
     "runtime": 1, "deadline": 5, "required_capacity": 1},
]

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

plan = create_fair_schedule(jobs, workers)

print("FAIR SCHEDULING ASSIGNMENTS")
for job in plan["assignments"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s | '
        f'Deadline met: {job["deadline_met"]}'
    )

print("\nUnscheduled jobs:")
for job in plan["unscheduled"]:
    print(job)

assert len(plan["assignments"]) + len(plan["unscheduled"]) == len(jobs)
print("\nFair scheduling engine test passed.")