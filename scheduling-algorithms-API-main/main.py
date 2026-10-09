
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.metrics import calculate_metrics


jobs = [
    {
        "id": "J01",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 8,
        "deadline": 30,
        "required_capacity": 1,
        "submitted_order": 1,
    },
    {
        "id": "J02",
        "tenant_id": "Team_B",
        "priority": "high",
        "runtime": 4,
        "deadline": 12,
        "required_capacity": 1,
        "submitted_order": 2,
    },
    {
        "id": "J03",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 6,
        "deadline": 25,
        "required_capacity": 2,
        "submitted_order": 3,
    },
    {
        "id": "J04",
        "tenant_id": "Team_B",
        "priority": "critical",
        "runtime": 3,
        "deadline": 8,
        "required_capacity": 1,
        "submitted_order": 4,
    },
]

workers = [
    {"id": "W1", "capacity": 2, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W3", "capacity": 1, "available_at": 0, "online": True},
]

start = perf_counter()
plan = create_schedule(jobs, workers)
elapsed_ms = (perf_counter() - start) * 1000

print("\n=== SCHEDULING PLAN ===")
for item in plan["assignments"]:
    print(
        f'{item["job_id"]} -> {item["worker_id"]} | '
        f'Start: {item["start_time"]}s | '
        f'Finish: {item["finish_time"]}s | '
        f'Deadline met: {item["deadline_met"]}'
    )

print("\n=== UNSCHEDULED JOBS ===")
for item in plan["unscheduled"]:
    print(item)

print("\n=== METRICS ===")
metrics = calculate_metrics(plan, workers, elapsed_ms)
for name, value in metrics.items():
    print(f"{name}: {value}")