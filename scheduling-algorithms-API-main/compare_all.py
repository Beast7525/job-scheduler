
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule
from scheduler.edf import edf_schedule
from scheduler.metrics import calculate_metrics


jobs = [
    {
        "id": "J01",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 10,
        "deadline": 30,
        "required_capacity": 1,
        "submitted_order": 1,
    },
    {
        "id": "J02",
        "tenant_id": "Team_B",
        "priority": "critical",
        "runtime": 2,
        "deadline": 3,
        "required_capacity": 1,
        "submitted_order": 2,
    },
    {
        "id": "J03",
        "tenant_id": "Team_A",
        "priority": "high",
        "runtime": 4,
        "deadline": 10,
        "required_capacity": 1,
        "submitted_order": 3,
    },
    {
        "id": "J04",
        "tenant_id": "Team_B",
        "priority": "low",
        "runtime": 3,
        "deadline": 20,
        "required_capacity": 1,
        "submitted_order": 4,
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


schedulers = {
    "FIFO": fifo_schedule,
    "EDF": edf_schedule,
    "Proposed": create_schedule,
}

for name, scheduler in schedulers.items():
    start = perf_counter()

    plan = scheduler(jobs, workers)

    elapsed_ms = (perf_counter() - start) * 1000
    metrics = calculate_metrics(plan, workers, elapsed_ms)

    print(f"\n{'=' * 40}")
    print(f"{name} SCHEDULER")
    print("=" * 40)

    for job in plan["assignments"]:
        print(
            f'{job["job_id"]} -> {job["worker_id"]} | '
            f'{job["start_time"]}-{job["finish_time"]}s | '
            f'Deadline met: {job["deadline_met"]}'
        )

    print("\nMetrics:")
    for metric, value in metrics.items():
        print(f"{metric}: {value}")