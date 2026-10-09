
from copy import deepcopy
from scheduler.engine import create_schedule


def replan_queued_jobs(jobs, workers, current_time, running_jobs=None):
    """
    Keep running jobs unchanged and schedule only queued jobs.

    running_jobs: jobs already in progress, each containing:
      job_id, tenant_id, worker_id, start_time, finish_time,
      deadline, priority
    """
    running_jobs = running_jobs or []

    updated_workers = deepcopy(workers)
    preserved_running = deepcopy(running_jobs)

    # Reserve worker time until each running job finishes.
    for running in preserved_running:
        for worker in updated_workers:
            if worker["id"] == running["worker_id"]:
                worker["available_at"] = max(
                    worker.get("available_at", current_time),
                    running["finish_time"]
                )

    running_ids = {job["job_id"] for job in preserved_running}

    # Only schedule jobs that have not started.
    queued_jobs = [
        job for job in jobs
        if job["id"] not in running_ids
    ]

    plan = create_schedule(
        queued_jobs,
        updated_workers,
        current_time=current_time
    )

    return {
        "running_jobs": preserved_running,
        "assignments": plan["assignments"],
        "unscheduled": plan["unscheduled"],
        "worker_timeline": plan["worker_timeline"],
    }