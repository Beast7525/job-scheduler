
from scheduler.baseline import create_schedule_in_order


def edf_schedule(jobs, workers, current_time=0):
    """
    Earliest Deadline First (EDF) scheduler.
    Jobs with earlier deadlines are scheduled first.
    """

    ordered_jobs = sorted(
        jobs,
        key=lambda job: (
            job["deadline"],
            job["runtime"],
            job["id"]
        )
    )

    return create_schedule_in_order(
        ordered_jobs,
        workers,
        current_time
    )