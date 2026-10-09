
from scheduler.fairness import fair_order_jobs
from scheduler.engine import create_schedule


def create_fair_schedule(jobs, workers, current_time=0):
    ordered_jobs = fair_order_jobs(jobs)

    return create_schedule(
        ordered_jobs,
        workers,
        current_time=current_time,
        preserve_order=True
    )