from db import db, get_db

_SIMULATION_TIME = 0.0


def get_current_simulation_time():
    return _SIMULATION_TIME


def set_simulation_time(new_time):
    global _SIMULATION_TIME
    _SIMULATION_TIME = float(new_time)
    return _SIMULATION_TIME


def advance_simulation_time(delta):
    global _SIMULATION_TIME
    _SIMULATION_TIME += float(delta)
    _process_simulation_tick(_SIMULATION_TIME)
    return _SIMULATION_TIME


def dispatch_assignment(job_id, worker_id, proposed_start=None):
    global _SIMULATION_TIME
    job = db.get_job(job_id)
    if not job:
        return False, f"Job '{job_id}' not found"

    if job["status"] not in ("queued", "scheduled"):
        return False, f"Job '{job_id}' is already {job['status']}"

    worker = db.get_worker(worker_id)
    if not worker:
        return False, f"Worker '{worker_id}' not found"

    if worker["status"] != "online":
        db.log_event(job_id=job_id, worker_id=worker_id, event_type="capacity_violation", sim_time=_SIMULATION_TIME, details={"reason": "Worker is offline"})
        return False, f"Worker '{worker_id}' is offline"

    if float(job["required_capacity"]) > float(worker["capacity"]):
        db.log_event(job_id=job_id, worker_id=worker_id, event_type="capacity_violation", sim_time=_SIMULATION_TIME, details={"reason": "Required capacity exceeds worker capacity"})
        return False, f"Job required capacity {job['required_capacity']} > worker capacity {worker['capacity']}"

    worker_avail = float(worker.get("available_at", 0))
    start_time = max(_SIMULATION_TIME, worker_avail) if proposed_start is None else float(proposed_start)
    if start_time < worker_avail:
        start_time = worker_avail

    finish_time = start_time + float(job["runtime_estimate"])
    deadline_met = 1 if finish_time <= float(job["deadline"]) else 0

    db.update_job(job_id, {
        "status": "running" if start_time <= _SIMULATION_TIME else "scheduled",
        "assigned_worker_id": worker_id,
        "available_at": finish_time,
        "start_time": start_time,
        "finish_time": finish_time,
        "deadline_met": deadline_met
    })

    db.update_worker(worker_id, {
        "available_at": finish_time,
        "current_job_id": job_id
    })

    db.log_event(
        job_id=job_id,
        worker_id=worker_id,
        event_type="job_assigned",
        sim_time=_SIMULATION_TIME,
        details={
            "start_time": start_time,
            "finish_time": finish_time,
            "deadline": job["deadline"],
            "deadline_met": bool(deadline_met)
        }
    )

    if finish_time <= _SIMULATION_TIME:
        _complete_job(job_id, worker_id, finish_time, deadline_met)

    return True, f"Job {job_id} assigned to worker {worker_id} (start: {start_time}, finish: {finish_time})"


def _complete_job(job_id, worker_id, finish_time, deadline_met):
    db.update_job(job_id, {
        "status": "completed",
        "finish_time": finish_time,
        "deadline_met": deadline_met
    })
    worker = db.get_worker(worker_id)
    if worker and worker.get("current_job_id") == job_id:
        db.update_worker(worker_id, {"current_job_id": None})

    db.log_event(
        job_id=job_id,
        worker_id=worker_id,
        event_type="job_completed",
        sim_time=finish_time,
        details={"deadline_met": bool(deadline_met)}
    )


def _process_simulation_tick(current_time):
    jobs = db.get_jobs()
    for job in jobs:
        if job["status"] == "scheduled" and job.get("start_time") is not None:
            if float(job["start_time"]) <= current_time:
                db.update_job(job["id"], {"status": "running"})
                db.log_event(job_id=job["id"], worker_id=job.get("assigned_worker_id"), event_type="job_started", sim_time=current_time)

        if job["status"] in ("running", "scheduled") and job.get("finish_time") is not None:
            if float(job["finish_time"]) <= current_time:
                _complete_job(job["id"], job.get("assigned_worker_id"), float(job["finish_time"]), job.get("deadline_met", 0))


def compute_metrics():
    global _SIMULATION_TIME
    jobs = db.get_jobs()
    workers = db.get_workers()

    total_jobs = len(jobs)
    completed_jobs = [j for j in jobs if j.get("status") == "completed"]
    queued_jobs = [j for j in jobs if j.get("status") == "queued"]
    running_jobs = [j for j in jobs if j.get("status") in ("running", "scheduled")]
    late_jobs = [j for j in jobs if j.get("deadline_met") == 0]

    completed_count = len(completed_jobs)
    deadline_met_count = sum(1 for j in completed_jobs if j.get("deadline_met") == 1)
    deadline_missed_count = completed_count - deadline_met_count

    compliance_rate = (deadline_met_count / completed_count) if completed_count > 0 else 1.0

    total_runtime = sum(float(j.get("runtime_estimate", 0)) for j in completed_jobs)
    num_workers = len(workers) if workers else 1
    max_window = max(_SIMULATION_TIME, 1.0)
    utilization = min(1.0, total_runtime / (num_workers * max_window))

    capacity_violations = 0
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) FROM execution_logs WHERE event_type = 'capacity_violation'").fetchone()
        if row:
            capacity_violations = row[0]

    return {
        "simulation_time": _SIMULATION_TIME,
        "totalJobs": total_jobs,
        "total_jobs": total_jobs,
        "completedJobs": completed_count,
        "completed_jobs": completed_count,
        "queuedJobs": len(queued_jobs),
        "queued_jobs": len(queued_jobs),
        "runningJobs": len(running_jobs),
        "running_jobs": len(running_jobs),
        "lateJobs": len(late_jobs),
        "late_jobs": len(late_jobs),
        "deadline_met_count": deadline_met_count,
        "deadline_missed_count": deadline_missed_count,
        "deadlineCompliance": round(compliance_rate * 100, 1),
        "deadline_compliance": round(compliance_rate * 100, 1),
        "workerUtilization": round(utilization * 100, 1),
        "utilization": round(utilization * 100, 1),
        "capacityViolations": capacity_violations,
        "capacity_violations": capacity_violations,
        "fairness_score": 1.0
    }
