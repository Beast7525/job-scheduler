
from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule

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
]

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
]


def show_result(title, scheduler):
    plan = scheduler(jobs, workers)
    print(f"\n=== {title} ===")

    for item in plan["assignments"]:
        print(
            f'{item["job_id"]}: '
            f'{item["start_time"]}s-{item["finish_time"]}s | '
            f'Deadline met: {item["deadline_met"]}'
        )

    print("Unscheduled:", plan["unscheduled"])

    met = sum(item["deadline_met"] for item in plan["assignments"])
    total = len(jobs)
    compliance = 100 * met / total if total else 100
    print(f"Deadline compliance: {compliance:.2f}%")


show_result("PRIORITY-BASED SCHEDULER", create_schedule)
show_result("FIFO BASELINE", fifo_schedule)