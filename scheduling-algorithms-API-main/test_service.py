
from scheduler.service import schedule_jobs

jobs = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 5,
        "deadline": 15,
        "required_capacity": 1,
        "submitted_order": 1,
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "priority": "critical",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
        "submitted_order": 2,
    },
]

workers = [
    {
        "id": "W1",
        "capacity": 1,
        "available_at": 0,
        "online": True,
    },
    {
        "id": "W2",
        "capacity": 1,
        "available_at": 0,
        "online": True,
    },
]

result = schedule_jobs(
    jobs=jobs,
    workers=workers,
    policy="proposed",
    current_time=0,
)

print("POLICY:", result["policy"])

print("\nASSIGNMENTS")
for assignment in result["assignments"]:
    print(
        f'{assignment["job_id"]} -> {assignment["worker_id"]} | '
        f'{assignment["start_time"]}-{assignment["finish_time"]}s'
    )

print("\nUNSCHEDULED")
for job in result["unscheduled"]:
    print(job)

print("\nMETRICS")
for key, value in result["metrics"].items():
    print(f"{key}: {value}")