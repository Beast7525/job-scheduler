
from scheduler.replanner import replan_queued_jobs

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
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
        "priority": "normal",
        "runtime": 4,
        "deadline": 12,
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

# J1 is already running on W1 and will finish at time 5.
running_jobs = [
    {
        "job_id": "J1",
        "tenant_id": "Team_A",
        "worker_id": "W1",
        "start_time": 0,
        "finish_time": 5,
        "deadline": 15,
        "priority": "normal",
    }
]

# A new critical job arrives at time 2.
new_job = {
    "id": "J4",
    "tenant_id": "Team_D",
    "priority": "critical",
    "runtime": 1,
    "deadline": 6,
    "required_capacity": 1,
}

jobs.append(new_job)

# W1 is still running J1; W2 remains available.
result = replan_queued_jobs(
    jobs=jobs,
    workers=workers,
    current_time=2,
    running_jobs=running_jobs,
)

print("PRESERVED RUNNING JOBS")
for job in result["running_jobs"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s'
    )

print("\nNEW PLAN FOR QUEUED JOBS")
for job in result["assignments"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s'
    )

print("\nUNSCHEDULED JOBS")
for job in result["unscheduled"]:
    print(f'{job["job_id"]}: {job["reason"]}')