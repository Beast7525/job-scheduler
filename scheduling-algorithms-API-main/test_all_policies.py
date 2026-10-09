from scheduler.service import schedule_jobs

jobs = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "runtime": 3,
        "deadline": 8,
        "required_capacity": 1,
        "priority": "critical",
        "submitted_order": 1
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "runtime": 4,
        "deadline": 12,
        "required_capacity": 1,
        "priority": "normal",
        "submitted_order": 2
    },
    {
        "id": "J3",
        "tenant_id": "Team_A",
        "runtime": 2,
        "deadline": 10,
        "required_capacity": 1,
        "priority": "high",
        "submitted_order": 3
    }
]

workers = [
    {"id": "W1", "capacity": 1, "online": True},
    {"id": "W2", "capacity": 2, "online": True}
]

policies = ["fifo", "edf", "proposed", "tenant_fair"]

print("\nSCHEDULING POLICY COMPARISON")
print("-" * 70)

for policy in policies:
    result = schedule_jobs(jobs, workers, policy=policy)

    metrics = result["metrics"]

    print(f"\nPolicy: {policy.upper()}")
    print(f"Assigned jobs: {metrics['assigned_jobs']}")
    print(f"Unscheduled jobs: {metrics['unscheduled_jobs']}")
    print(
        "Deadline compliance: "
        f"{metrics['deadline_compliance_percent']}%"
    )
    print(
        "Worker utilization: "
        f"{metrics['worker_utilization_percent']}%"
    )
    print(
        "Tenant fairness: "
        f"{metrics['tenant_distribution_fairness']}"
    )