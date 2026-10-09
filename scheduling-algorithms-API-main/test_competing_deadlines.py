from scheduler.service import schedule_jobs

jobs = [
    {
        "id": "URGENT",
        "tenant_id": "Team_A",
        "runtime": 4,
        "deadline": 3,
        "required_capacity": 1,
        "priority": "critical",
        "submitted_order": 1
    },
    {
        "id": "NORMAL",
        "tenant_id": "Team_B",
        "runtime": 2,
        "deadline": 10,
        "required_capacity": 1,
        "priority": "normal",
        "submitted_order": 2
    },
    {
        "id": "SHORT",
        "tenant_id": "Team_C",
        "runtime": 1,
        "deadline": 5,
        "required_capacity": 1,
        "priority": "high",
        "submitted_order": 3
    }
]

workers = [
    {"id": "W1", "capacity": 1, "online": True}
]

for policy in ["fifo", "edf", "proposed", "tenant_fair"]:
    result = schedule_jobs(jobs, workers, policy=policy)

    print(f"\n{'=' * 45}")
    print(f"POLICY: {policy.upper()}")

    for assignment in result["assignments"]:
        print(
            f"{assignment['job_id']}: "
            f"{assignment['start_time']} -> "
            f"{assignment['finish_time']}, "
            f"deadline={assignment['deadline']}, "
            f"met={assignment['deadline_met']}"
        )

    for item in result["unscheduled"]:
        print(f"Unscheduled: {item}")

    print(
        "Deadline compliance:",
        result["metrics"]["deadline_compliance_percent"],
        "%"
    )