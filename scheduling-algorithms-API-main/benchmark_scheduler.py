from scheduler.service import schedule_jobs

JOBS = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "runtime": 4,
        "deadline": 5,
        "required_capacity": 1,
        "priority": "critical",
        "submitted_order": 1,
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "runtime": 2,
        "deadline": 4,
        "required_capacity": 1,
        "priority": "high",
        "submitted_order": 2,
    },
    {
        "id": "J3",
        "tenant_id": "Team_C",
        "runtime": 3,
        "deadline": 10,
        "required_capacity": 1,
        "priority": "normal",
        "submitted_order": 3,
    },
    {
        "id": "J4",
        "tenant_id": "Team_A",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
        "priority": "normal",
        "submitted_order": 4,
    },
    {
        "id": "J5",
        "tenant_id": "Team_B",
        "runtime": 5,
        "deadline": 12,
        "required_capacity": 2,
        "priority": "low",
        "submitted_order": 5,
    },
]

WORKERS = [
    {"id": "W1", "capacity": 1, "online": True},
    {"id": "W2", "capacity": 2, "online": True},
]

POLICIES = ["fifo", "edf", "proposed", "tenant_fair"]


def main():
    print("\nHORIZON D05 - SCHEDULER BENCHMARK")
    print("=" * 78)
    print(
        f"{'Policy':<14} {'Assigned':<10} {'Unscheduled':<13} "
        f"{'Deadline %':<12} {'Utilization %':<15} {'Fairness':<10}"
    )
    print("-" * 78)

    for policy in POLICIES:
        result = schedule_jobs(
            jobs=JOBS,
            workers=WORKERS,
            policy=policy,
            current_time=0,
        )

        metrics = result["metrics"]

        print(
            f"{policy:<14} "
            f"{metrics['assigned_jobs']:<10} "
            f"{metrics['unscheduled_jobs']:<13} "
            f"{metrics['deadline_compliance_percent']:<12.2f} "
            f"{metrics['worker_utilization_percent']:<15.2f} "
            f"{metrics['tenant_distribution_fairness']:<10.3f}"
        )


if __name__ == "__main__":
    main()