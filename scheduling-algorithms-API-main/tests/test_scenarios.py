
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule
from scheduler.edf import edf_schedule
from scheduler.metrics import calculate_metrics


SCHEDULERS = {
    "FIFO": fifo_schedule,
    "EDF": edf_schedule,
    "PROPOSED": create_schedule,
}


def make_job(job_id, tenant, priority, runtime, deadline, capacity, order):
    return {
        "id": job_id,
        "tenant_id": tenant,
        "priority": priority,
        "runtime": runtime,
        "deadline": deadline,
        "required_capacity": capacity,
        "submitted_order": order,
    }


SCENARIOS = [
    {
        "name": "1. Tight Deadlines",
        "description": "An urgent short job competes with a long job.",
        "current_time": 0,
        "jobs": [
            make_job("J01", "Team_A", "normal", 10, 30, 1, 1),
            make_job("J02", "Team_B", "critical", 2, 3, 1, 2),
        ],
        "workers": [
            {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
        ],
    },
    {
        "name": "2. Worker Offline",
        "description": "One worker is offline, so jobs must use an available worker.",
        "current_time": 0,
        "jobs": [
            make_job("J01", "Team_A", "high", 4, 10, 1, 1),
            make_job("J02", "Team_B", "normal", 3, 12, 1, 2),
        ],
        "workers": [
            {"id": "W1", "capacity": 2, "available_at": 0, "online": False},
            {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
        ],
    },
    {
        "name": "3. Insufficient Capacity",
        "description": "One job needs more capacity than any worker provides.",
        "current_time": 0,
        "jobs": [
            make_job("J01", "Team_A", "high", 5, 15, 2, 1),
            make_job("J02", "Team_B", "normal", 3, 10, 1, 2),
        ],
        "workers": [
            {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
            {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
        ],
    },
    {
        "name": "4. Heavy Workload",
        "description": "Twelve jobs compete for three workers.",
        "current_time": 0,
        "jobs": [
            make_job(
                f"J{i:02d}",
                f"Team_{'ABC'[i % 3]}",
                ["critical", "high", "normal", "low"][i % 4],
                [3, 6, 2, 5][i % 4],
                [5, 12, 18, 25][i % 4] + i,
                1 if i % 3 else 2,
                i,
            )
            for i in range(1, 13)
        ],
        "workers": [
            {"id": "W1", "capacity": 2, "available_at": 0, "online": True},
            {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
            {"id": "W3", "capacity": 2, "available_at": 0, "online": True},
        ],
    },
    {
        "name": "5. Urgent Job Arrival",
        "description": "A new urgent job arrives when workers are already busy.",
        "current_time": 3,
        "jobs": [
            make_job("J03", "Team_C", "critical", 2, 8, 1, 3),
        ],
        "workers": [
            {"id": "W1", "capacity": 1, "available_at": 10, "online": True},
            {"id": "W2", "capacity": 1, "available_at": 8, "online": True},
        ],
    },
]


def run_scenario(scenario):
    print("\n" + "=" * 65)
    print(scenario["name"])
    print(scenario["description"])
    print("=" * 65)

    for name, scheduler in SCHEDULERS.items():
        start = perf_counter()

        plan = scheduler(
            scenario["jobs"],
            scenario["workers"],
            current_time=scenario["current_time"],
        )

        elapsed_ms = (perf_counter() - start) * 1000
        metrics = calculate_metrics(
            plan, scenario["workers"], elapsed_ms
        )

        print(f"\n--- {name} SCHEDULER ---")

        for job in plan["assignments"]:
            print(
                f'{job["job_id"]} -> {job["worker_id"]} | '
                f'{job["start_time"]}-{job["finish_time"]}s | '
                f'Deadline met: {job["deadline_met"]}'
            )

        if plan["unscheduled"]:
            print("Unscheduled jobs:")
            for job in plan["unscheduled"]:
                print(f'  {job["job_id"]}: {job["reason"]}')

        print(
            f'Deadline compliance: '
            f'{metrics["deadline_compliance_percent"]}%'
        )
        print(f'Assigned: {metrics["assigned_jobs"]}')
        print(f'Unscheduled: {metrics["unscheduled_jobs"]}')
        print(
            f'Worker utilization: '
            f'{metrics["worker_utilization_percent"]}%'
        )


if __name__ == "__main__":
    for scenario in SCENARIOS:
        run_scenario(scenario)

    print("\nAll five scenarios have finished running.")