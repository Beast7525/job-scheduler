
from copy import deepcopy
from scheduler.engine import create_schedule

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

jobs = [
    {
        "id": "J1",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 5,
        "deadline": 15,
        "required_capacity": 1,
    },
    {
        "id": "J2",
        "tenant_id": "Team_B",
        "priority": "normal",
        "runtime": 4,
        "deadline": 12,
        "required_capacity": 1,
    },
    {
        "id": "J3",
        "tenant_id": "Team_C",
        "priority": "critical",
        "runtime": 2,
        "deadline": 8,
        "required_capacity": 1,
    },
]


def show_plan(title, plan):
    print("\n" + "=" * 45)
    print(title)
    print("=" * 45)

    for job in plan["assignments"]:
        print(
            f'{job["job_id"]} -> {job["worker_id"]} | '
            f'{job["start_time"]}-{job["finish_time"]}s'
        )

    for job in plan["unscheduled"]:
        print(
            f'{job["job_id"]} -> UNSCHEDULED | '
            f'{job["reason"]}'
        )


# 1. Initial schedule
initial_plan = create_schedule(
    jobs, deepcopy(workers), current_time=0
)
show_plan("INITIAL SCHEDULE", initial_plan)


# 2. Worker W1 goes offline.
# Replan the workload using only the remaining online worker.
updated_workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": False},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

offline_plan = create_schedule(
    jobs, deepcopy(updated_workers), current_time=0
)
show_plan("REPLAN AFTER W1 GOES OFFLINE", offline_plan)


# 3. A new critical job arrives at time 0.
new_jobs = jobs + [
    {
        "id": "J4",
        "tenant_id": "Team_D",
        "priority": "critical",
        "runtime": 1,
        "deadline": 3,
        "required_capacity": 1,
    }
]

urgent_plan = create_schedule(
    new_jobs, deepcopy(workers), current_time=0
)
show_plan("REPLAN AFTER URGENT JOB ARRIVES", urgent_plan)