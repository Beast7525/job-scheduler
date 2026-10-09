
from scheduler.replanner import replan_queued_jobs

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": False},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

jobs = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 5,
        "deadline": 15,
        "required_capacity": 1,
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "priority": "high",
        "runtime": 3,
        "deadline": 10,
        "required_capacity": 1,
    },
    {
        "id": "J3",
        "tenant_id": "Team_C",
        "priority": "critical",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
    },
]

# J1 was running on W1 when that worker failed at time 2.
# It is deliberately NOT included as a preserved running job.
# This test models J1 as interrupted and queued for a full retry.
current_time = 2

result = replan_queued_jobs(
    jobs=jobs,
    workers=workers,
    current_time=current_time,
    running_jobs=[],
)

print("WORKER STATUS")
for worker in workers:
    print(f'{worker["id"]}: {"ONLINE" if worker["online"] else "OFFLINE"}')

print("\nREVISED SCHEDULE")
for job in result["assignments"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s'
    )

print("\nUNSCHEDULED JOBS")
for job in result["unscheduled"]:
    print(f'{job["job_id"]}: {job["reason"]}')