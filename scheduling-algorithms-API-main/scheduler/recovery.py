
from copy import deepcopy


def recover_failed_jobs(jobs, failed_job_ids, max_retries=2):
    """
    Requeue failed jobs and track retry attempts.

    Each job may optionally contain:
      retry_count: number of retries already attempted
    """
    recovered_jobs = []
    failed_jobs = []

    for original_job in jobs:
        job = deepcopy(original_job)

        if job["id"] not in failed_job_ids:
            recovered_jobs.append(job)
            continue

        retries = job.get("retry_count", 0)

        if retries < max_retries:
            job["retry_count"] = retries + 1
            job["status"] = "queued"
            job["recovery_reason"] = "worker_failure"
            recovered_jobs.append(job)
        else:
            job["status"] = "failed"
            job["recovery_reason"] = "retry_limit_exceeded"
            failed_jobs.append(job)

    return {
        "queued_jobs": recovered_jobs,
        "failed_jobs": failed_jobs,
    }