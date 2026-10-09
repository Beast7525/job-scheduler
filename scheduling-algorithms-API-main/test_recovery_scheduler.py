
from scheduler.recovery import recover_failed_jobs
from scheduler.engine import create_schedule

# W1 has failed; W2 is available for scheduling.
workers = [
    {
        "id": "W1",
        "capacity": 1,
        "available_at": 0,
        "online": False,
    },
    {
        "id": "W2",
        "capacity": 1,
        "available_at": 0,
        "online": True,
    },
]

jobs = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 5,
        "deadline": 15,
        "required_capacity": 1,
        "retry_count": 0,
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "priority": "high",
        "runtime": 3,
        "deadline": 10,
        "required_capacity": 1,
        "retry_count": 1,
    },
    {
        "id": "J3",
        "tenant_id": "Team_C",
        "priority": "critical",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
        "retry_count": 2,
    },
]

# Step 1: Recover failed jobs.
recovery = recover_failed_jobs(
    jobs,
    failed_job_ids={"J1", "J2", "J3"},
    max_retries=2,
)

# Step 2: Schedule only jobs that are eligible for retry.
queued_jobs = recovery["queued_jobs"]

plan = create_schedule(
    queued_jobs,
    workers,
    current_time=2,
)

print("\nRECOVERY SUMMARY")
print("Jobs eligible for retry:", len(queued_jobs))
print("Jobs permanently failed:", len(recovery["failed_jobs"]))

print("\nRETRIED JOB SCHEDULE")
for assignment in plan["assignments"]:
    print(
        f'{assignment["job_id"]} -> {assignment["worker_id"]} | '
        f'{assignment["start_time"]}-{assignment["finish_time"]}s'
    )

print("\nUNSCHEDULED RETRIES")
for job in plan["unscheduled"]:
    print(f'{job["job_id"]}: {job["reason"]}')

print("\nJOBS EXHAUSTING RETRY LIMIT")
for job in recovery["failed_jobs"]:
    print(f'{job["id"]}: {job["recovery_reason"]}')