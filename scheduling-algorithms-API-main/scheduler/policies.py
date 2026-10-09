
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}


def job_sort_key(job):
    """Return the scheduling order for a queued job."""
    priority = PRIORITY_ORDER.get(
        job.get("priority", "normal").lower(), 2
    )

    return (
        priority,
        job["deadline"],
        job["runtime"],
        job["id"],
    )


def sort_jobs(jobs):
    """Return a new list in scheduling order."""
    return sorted(jobs, key=job_sort_key)