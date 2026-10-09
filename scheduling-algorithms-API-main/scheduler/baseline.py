
from scheduler.engine import create_schedule


def fifo_schedule(jobs, workers, current_time=0):
    """
    Baseline: schedule jobs in submission order.
    """
    ordered_jobs = sorted(
        jobs,
        key=lambda job: job.get("submitted_order", 0),
    )

    return create_schedule_in_order(
        ordered_jobs, workers, current_time
    )


def create_schedule_in_order(jobs, workers, current_time=0):
    # Reuse the engine's assignment mechanics while preserving
    # the FIFO order rather than applying priority sorting.
    worker_state = [dict(w) for w in workers]
    assignments = []
    unscheduled = []

    for job in jobs:
        candidates = []

        for worker in worker_state:
            if not worker.get("online", True):
                continue
            if job["required_capacity"] > worker["capacity"]:
                continue

            start = max(
                current_time,
                worker.get("available_at", current_time),
            )
            candidates.append({
                "worker": worker,
                "start": start,
                "finish": start + job["runtime"],
            })

        if not candidates:
            unscheduled.append({
                "job_id": job["id"],
                "reason": "No compatible online worker",
            })
            continue

        chosen = min(
            candidates,
            key=lambda c: (c["finish"], c["worker"]["id"]),
        )

        worker = chosen["worker"]
        finish = chosen["finish"]

        assignments.append({
            "job_id": job["id"],
            "tenant_id": job.get("tenant_id", "default"),
            "worker_id": worker["id"],
            "start_time": chosen["start"],
            "finish_time": finish,
            "deadline": job["deadline"],
            "priority": job.get("priority", "normal"),
            "deadline_met": finish <= job["deadline"],
            "status": "planned",
        })

        worker["available_at"] = finish

    return {
        "assignments": assignments,
        "unscheduled": unscheduled,
    }