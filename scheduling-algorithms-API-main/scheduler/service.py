
from time import perf_counter

from scheduler.engine import create_schedule
from scheduler.baseline import fifo_schedule
from scheduler.edf import edf_schedule
from scheduler.fair_engine import create_fair_schedule
from scheduler.metrics import calculate_metrics


SCHEDULERS = {
    "proposed": create_schedule,
    "fifo": fifo_schedule,
    "edf": edf_schedule,
    "tenant_fair": create_fair_schedule,
}


def schedule_jobs(jobs, workers, policy="proposed", current_time=0):
    """
    Main service interface for the backend.

    Returns the selected scheduling plan and its metrics.
    """
    if policy not in SCHEDULERS:
        raise ValueError(
            f"Unknown policy '{policy}'. "
            f"Choose from: {', '.join(SCHEDULERS)}"
        )

    start = perf_counter()

    plan = SCHEDULERS[policy](
        jobs,
        workers,
        current_time=current_time,
    )

    elapsed_ms = (perf_counter() - start) * 1000
    metrics = calculate_metrics(plan, workers, elapsed_ms)

    return {
        "policy": policy,
        "current_time": current_time,
        "assignments": plan["assignments"],
        "unscheduled": plan["unscheduled"],
        "metrics": metrics,
    }