import time
from db import db
from services.execution_service import dispatch_assignment, get_current_simulation_time

PRIORITY_WEIGHTS = {
    "critical": 4,
    "high": 3,
    "normal": 2,
    "low": 1
}


def create_schedule(jobs=None, workers=None, current_time=None):
    """
    Member 2 shared contract adapter.
    Input:
        jobs: list of job dicts (or None to load queued jobs from DB)
        workers: list of worker dicts (or None to load workers from DB)
        current_time: numeric simulation time (or None to use current sim time)

    Output:
        Plan dictionary containing assignments, predicted finish times, and risk metrics.
    """
    start_ts = time.perf_counter()
    if current_time is None:
        current_time = get_current_simulation_time()

    if jobs is None:
        jobs = db.get_jobs(status="queued")
    else:
        # Filter for queued jobs
        jobs = [j for j in jobs if j.get("status") == "queued"]

    if workers is None:
        workers = db.get_workers()

    online_workers = [w for w in workers if w.get("status") == "online"]

    # Calculate slack and rank queued jobs by priority (desc) then slack (asc)
    ranked_jobs = []
    for job in jobs:
        runtime = float(job["runtime_estimate"])
        deadline = float(job["deadline"])
        slack = deadline - (current_time + runtime)
        prio_val = PRIORITY_WEIGHTS.get(str(job.get("priority", "normal")).lower(), 2)
        ranked_jobs.append({
            "job": job,
            "slack": slack,
            "priority_val": prio_val
        })

    # Sort: higher priority value first, then smaller slack (tighter deadline)
    ranked_jobs.sort(key=lambda x: (-x["priority_val"], x["slack"]))

    # Virtual worker state to calculate assignments
    worker_avail_map = {w["id"]: float(w.get("available_at", current_time)) for w in online_workers}
    worker_cap_map = {w["id"]: float(w["capacity"]) for w in online_workers}

    assignments = []
    deadline_met_count = 0
    deadline_missed_count = 0
    capacity_violations = 0

    dispatched_jobs = []

    for item in ranked_jobs:
        job = item["job"]
        req_cap = float(job["required_capacity"])
        assigned_worker_id = None
        earliest_start = float("inf")

        # Find eligible online worker with lowest available_at time
        for w_id in online_workers:
            wid = w_id["id"]
            if req_cap <= worker_cap_map[wid]:
                avail = max(current_time, worker_avail_map[wid])
                if avail < earliest_start:
                    earliest_start = avail
                    assigned_worker_id = wid

        if assigned_worker_id is not None:
            finish_time = earliest_start + float(job["runtime_estimate"])
            deadline_met = finish_time <= float(job["deadline"])

            if deadline_met:
                deadline_met_count += 1
            else:
                deadline_missed_count += 1

            # Update virtual availability
            worker_avail_map[assigned_worker_id] = finish_time

            assignment = {
                "job_id": job["id"],
                "worker_id": assigned_worker_id,
                "start_time": earliest_start,
                "predicted_finish": finish_time,
                "deadline_met": deadline_met
            }
            assignments.append(assignment)

            # Dispatch assignment in execution engine
            success, msg = dispatch_assignment(job["id"], assigned_worker_id, proposed_start=earliest_start)
            if success:
                dispatched_jobs.append(job["id"])
        else:
            capacity_violations += 1
            db.log_event(
                job_id=job["id"],
                worker_id=None,
                event_type="scheduling_rejection",
                sim_time=current_time,
                details={"reason": "No online worker available with required capacity"}
            )

    elapsed_ms = round((time.perf_counter() - start_ts) * 1000, 2)

    plan = {
        "algorithm_name": "priority_slack_scheduler",
        "simulation_time": current_time,
        "planning_duration_ms": elapsed_ms,
        "assignments": assignments,
        "deadline_met_count": deadline_met_count,
        "deadline_missed_count": deadline_missed_count,
        "capacity_violations": capacity_violations,
        "dispatched_jobs_count": len(dispatched_jobs)
    }

    # Record scheduling run
    db.record_scheduling_run({
        "algorithm_name": "priority_slack_scheduler",
        "simulation_time": current_time,
        "planning_duration_ms": elapsed_ms,
        "deadline_met_count": deadline_met_count,
        "deadline_missed_count": deadline_missed_count,
        "utilization": 0.0,
        "fairness_score": 1.0,
        "capacity_violations": capacity_violations,
        "result": plan
    })

    return plan
