
from scheduler.recovery import recover_failed_jobs

jobs = [
    {
        "id": "J1",
        "priority": "normal",
        "runtime": 5,
        "deadline": 15,
        "required_capacity": 1,
        "retry_count": 0,
    },
    {
        "id": "J2",
        "priority": "high",
        "runtime": 3,
        "deadline": 10,
        "required_capacity": 1,
        "retry_count": 1,
    },
    {
        "id": "J3",
        "priority": "critical",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
        "retry_count": 2,
    },
]

result = recover_failed_jobs(
    jobs,
    failed_job_ids={"J1", "J2", "J3"},
    max_retries=2,
)

print("JOBS READY FOR RETRY")
for job in result["queued_jobs"]:
    print(
        f'{job["id"]} | retries={job.get("retry_count", 0)} | '
        f'status={job.get("status", "queued")}'
    )

print("\nJOBS THAT EXCEEDED RETRY LIMIT")
for job in result["failed_jobs"]:
    print(
        f'{job["id"]} | retries={job["retry_count"]} | '
        f'status={job["status"]} | {job["recovery_reason"]}'
    )