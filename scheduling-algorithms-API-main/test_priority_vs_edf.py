
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.edf import edf_schedule
from scheduler.metrics import calculate_metrics

# Same jobs and worker for both scheduling policies
jobs = [
    {
        "id": "N1",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
        "submitted_order": 1,
    },
    {
        "id": "C1",
        "tenant_id": "Team_B",
        "priority": "critical",
        "runtime": 2,
        "deadline": 10,
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
    }
]

schedulers = {
    "EDF": edf_schedule,
    "PROPOSED": create_schedule,
}

for name, scheduler in schedulers.items():
    start = perf_counter()
    plan = scheduler(jobs, workers)
    elapsed_ms = (perf_counter() - start) * 1000

    metrics = calculate_metrics(plan, workers, elapsed_ms)

    print("\n" + "=" * 35)
    print(f"{name} SCHEDULER")
    print("=" * 35)

    for job in plan["assignments"]:
        print(
            f'{job["job_id"]} | '
            f'{job["start_time"]}-{job["finish_time"]}s | '
            f'Priority: {job["priority"]} | '
            f'Deadline met: {job["deadline_met"]}'
        )

    print("\nDeadline compliance:",
          metrics["deadline_compliance_percent"], "%")
    print("Assigned jobs:", metrics["assigned_jobs"])
    print("Unscheduled jobs:", metrics["unscheduled_jobs"])