from db import db

DEFAULT_WORKERS = [
    {"id": "W1", "name": "Worker 1", "capacity": 2, "available_at": 0, "status": "online"},
    {"id": "W2", "name": "Worker 2", "capacity": 2, "available_at": 0, "status": "online"},
    {"id": "W3", "name": "Worker 3", "capacity": 2, "available_at": 0, "status": "online"},
]


def initialize_workers():
    existing = db.get_workers()
    existing_ids = {w["id"] for w in existing}
    missing = [w for w in DEFAULT_WORKERS if w["id"] not in existing_ids]

    if missing:
        db.upsert_workers(missing)

    return db.get_workers()


def list_workers():
    workers = db.get_workers()
    if not workers:
        return initialize_workers()
    return workers


def get_worker_by_id(worker_id):
    worker = db.get_worker(worker_id)
    if not worker:
        return None, {"error": f"Worker '{worker_id}' not found"}, 404
    return worker, None, 200


def update_worker_capacity(worker_id, new_capacity):
    try:
        cap = float(new_capacity)
        if cap <= 0:
            return None, {"error": "Capacity must be greater than zero"}, 400
    except (TypeError, ValueError):
        return None, {"error": "Capacity must be a valid number"}, 400

    worker, err, status_code = get_worker_by_id(worker_id)
    if err:
        return None, err, status_code

    db.update_worker(worker_id, {"capacity": cap})
    db.log_event(job_id=None, worker_id=worker_id, event_type="worker_capacity_changed", details={"old_capacity": worker["capacity"], "new_capacity": cap})
    return db.get_worker(worker_id), None, 200


def set_worker_failure(worker_id, sim_time=0):
    worker, err, status_code = get_worker_by_id(worker_id)
    if err:
        return None, err, status_code

    db.update_worker(worker_id, {"status": "offline"})
    db.log_event(job_id=None, worker_id=worker_id, event_type="worker_failed", sim_time=sim_time, details={"previous_status": worker["status"]})
    return db.get_worker(worker_id), None, 200


def set_worker_recovery(worker_id, sim_time=0):
    worker, err, status_code = get_worker_by_id(worker_id)
    if err:
        return None, err, status_code

    db.update_worker(worker_id, {"status": "online"})
    db.log_event(job_id=None, worker_id=worker_id, event_type="worker_recovered", sim_time=sim_time, details={"previous_status": worker["status"]})
    return db.get_worker(worker_id), None, 200


def reset_simulation():
    db.reset_all()
    workers = initialize_workers()
    db.log_event(job_id=None, worker_id=None, event_type="simulation_reset", sim_time=0, details={"message": "Simulation reset completed"})
    return {"status": "reset_successful", "workers": workers}
