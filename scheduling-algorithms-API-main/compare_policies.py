
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule
from scheduler.edf import edf_schedule
from scheduler.fair_engine import create_fair_schedule
from scheduler.metrics import calculate_metrics


jobs = [
    {"id": "A1", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 8, "deadline": 25, "required_capacity": 1, "submitted_order": 1},
    {"id": "A2", "tenant_id": "Team_A", "priority": "high",
     "runtime": 5, "deadline": 15, "required_capacity": 1, "submitted_order": 2},
    {"id": "A3", "tenant_id": "Team_A", "priority": "normal",
     "runtime": 6, "deadline": 30, "required_capacity": 1, "submitted_order": 3},
    {"id": "B1", "tenant_id": "Team_B", "priority": "critical",
     "runtime": 2, "deadline": 5, "required_capacity": 1, "submitted_order": 4},
    {"id": "B2", "tenant_id": "Team_B", "priority": "normal",
     "runtime": 4, "deadline": 18, "required_capacity": 1, "submitted_order": 5},
    {"id": "C1", "tenant_id": "Team_C", "priority": "high",
     "runtime": 3, "deadline": 12, "required_capacity": 1, "submitted_order": 6},
]

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

schedulers = {
    "FIFO": fifo_schedule,
    "EDF": edf_schedule,
    "PROPOSED": create_schedule,
    "TENANT-FAIR": create_fair_schedule,
}

for name, scheduler in schedulers.items():
    start = perf_counter()

    plan = scheduler(jobs, workers)

    elapsed_ms = (perf_counter() - start) * 1000
    metrics = calculate_metrics(plan, workers, elapsed_ms)

    print("\n" + "=" * 45)
    print(f"{name} SCHEDULER")
    print("=" * 45)

    for job in plan["assignments"]:
        print(
            f'{job["job_id"]} -> {job["worker_id"]} | '
            f'{job["start_time"]}-{job["finish_time"]}s | '
            f'Deadline met: {job["deadline_met"]}'
        )

    print("\nMetrics:")
    for metric, value in metrics.items():
        print(f"{metric}: {value}")