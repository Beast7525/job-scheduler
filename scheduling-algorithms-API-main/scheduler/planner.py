def can_run(job, worker):
    """Check basic worker eligibility."""

    return (
        worker["status"] == "online"
        and worker["capacity"] >= job["required_capacity"]
    )


def estimate_finish(job, worker, current_time):
    """Estimate start and finish times."""

    start_time = max(
        current_time,
        worker.get("available_at", current_time),
    )

    finish_time = start_time + job["runtime_estimate"]

    return start_time, finish_time


def is_deadline_feasible(job, finish_time):
    """Check whether estimated completion meets the deadline."""

    return finish_time <= job["deadline"]
