
from scheduler.engine import create_schedule

workers = [
    {"id": "W1", "capacity": 1, "available_at": 0, "online": True},
    {"id": "W2", "capacity": 1, "available_at": 0, "online": True},
]

# Initial jobs
initial_jobs = [
    {
        "id": "J01",
        "tenant_id": "Team_A",
        "priority": "normal",
        "runtime": 10,
        "deadline": 30,
        "required_capacity": 1,
    },
    {
        "id": "J02",
        "tenant_id": "Team_B",
        "priority": "normal",
        "runtime": 8,
        "deadline": 30,
        "required_capacity": 1,
    },
]

initial_plan = create_schedule(initial_jobs, workers)

print("=== INITIAL PLAN ===")
for job in initial_plan["assignments"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s'
    )

# Simulation has now advanced to t=3.
# Assume J01 is running on W1, J02 is running on W2.
# Preserve both running jobs; schedule only the new queued job.
urgent_job = {
    "id": "J03",
    "tenant_id": "Team_C",
    "priority": "critical",
    "runtime": 2,
    "deadline": 8,
    "required_capacity": 1,
}

current_time = 3

remaining_workers = [
    {
        "id": "W1",
        "capacity": 1,
        "available_at": 10,  # J01 is already running
        "online": True,
    },
    {
        "id": "W2",
        "capacity": 1,
        "available_at": 8,   # J02 is already running
        "online": True,
    },
]

new_plan = create_schedule(
    [urgent_job],
    remaining_workers,
    current_time=current_time,
)

print("\n=== REPLANNED QUEUED JOBS ===")
for job in new_plan["assignments"]:
    print(
        f'{job["job_id"]} -> {job["worker_id"]} | '
        f'{job["start_time"]}-{job["finish_time"]}s | '
        f'Deadline met: {job["deadline_met"]}'
    )