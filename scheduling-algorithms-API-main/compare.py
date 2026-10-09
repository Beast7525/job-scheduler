
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule
from scheduler.metrics import calculate_metrics

jobs = [
    {
        "id": "J01", "tenant_id": "Team_A",
        "priority": "normal", "runtime": 8,
        "deadline": 30, "required_capacity": 1,
        "submitted_order": 1,
    },
    {
        "id": "J02", "tenant_id": "Team_B",
        "priority": "high", "runtime": 4,
        "deadline": 12, "required_capacity": 1,
        "submitted_order": 2,
    },
    {
        "id": "J03", "tenant_id": "Team_A",
        "priority": "normal", "runtime": 6,
        "deadline": 25, "required_capacity": 2,
        "submitted_order": 3,
    },
    {
        "id": "J04", "tenant_id": "Team_B",
        "priority": "critical", "runtime": 3,
        "deadline": 8, "required_capacity": 1,
        "submitted_order": 4,
    },
]

workers = [
    {"id": "W1", "capacity": 2, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W3", "capacity": 1, "available_at": 0, "online": True},
]


def run_scheduler(name, scheduler_function):
    start = perf_counter()
    plan = scheduler_function(jobs, workers)
    elapsed_ms = (perf_counter() - start) * 1000

    metrics = calculate_metrics(plan, workers, elapsed_ms)

    print(f"\n=== {name} ===")

    for item in plan["assignments"]:
        print(
            f'{item["job_id"]} -> {item["worker_id"]} | '
            f'{item["start_time"]}s-{item["finish_time"]}s | '
            f'Deadline met: {item["deadline_met"]}'
        )

    print("\nMetrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    return metrics


priority_metrics = run_scheduler(
    "PRIORITY-BASED SCHEDULER",
    create_schedule,
)

fifo_metrics = run_scheduler(
    "FIFO BASELINE",
    fifo_schedule,
)

print("\n=== COMPARISON ===")
print(
    "Priority deadline compliance:",
    priority_metrics["deadline_compliance_percent"], "%",
)
print(
    "FIFO deadline compliance:",
    fifo_metrics["deadline_compliance_percent"], "%",
)