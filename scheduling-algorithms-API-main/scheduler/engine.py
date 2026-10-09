
from scheduler.policies import sort_jobs


def create_schedule(jobs, workers, current_time=0, preserve_order=False):
    ordered_jobs = (
        list(jobs) if preserve_order else sort_jobs(jobs)
    )
    worker_state = [dict(w) for w in workers]

    assignments = []
    unscheduled = []
    worker_timeline = {w["id"]: [] for w in worker_state}

    for job in ordered_jobs:
        candidates = []

        for worker in worker_state:
            if not worker.get("online", True):
                continue

            if job["required_capacity"] > worker["capacity"]:
                continue

            start = max(
                current_time,
                worker.get("available_at", current_time)
            )
            finish = start + job["runtime"]

            candidates.append({
                "worker": worker,
                "start": start,
                "finish": finish
            })

        if not candidates:
            unscheduled.append({
                "job_id": job["id"],
                "reason": "no_compatible_worker",
                "detail": "No online worker has sufficient capacity"
            })
            continue

        chosen = min(
            candidates,
            key=lambda c: (
                c["finish"],
                c["start"],
                c["worker"]["id"]
            )
        )

        worker = chosen["worker"]
        start = chosen["start"]
        finish = chosen["finish"]

        if finish > job["deadline"]:
            unscheduled.append({
                "job_id": job["id"],
                "reason": "deadline_infeasible",
                "earliest_finish": finish,
                "deadline": job["deadline"]
            })
            continue

        assignment = {
            "job_id": job["id"],
            "tenant_id": job.get("tenant_id", "default"),
            "worker_id": worker["id"],
            "start_time": start,
            "finish_time": finish,
            "deadline": job["deadline"],
            "priority": job.get("priority", "normal"),
            "deadline_met": True,
            "status": "planned"
        }

        assignments.append(assignment)
        worker_timeline[worker["id"]].append(assignment)
        worker["available_at"] = finish

    return {
        "assignments": assignments,
        "unscheduled": unscheduled,
        "worker_timeline": worker_timeline
    }