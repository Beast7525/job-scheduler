import datetime
import time
from db import db

VALID_PRIORITIES = {"critical", "high", "normal", "low"}
VALID_STATUSES = {"queued", "scheduled", "running", "completed", "failed", "interrupted", "cancelled"}


def _parse_deadline(deadline_val):
    if deadline_val is None:
        raise ValueError("Deadline is required")
    if isinstance(deadline_val, (int, float)):
        return float(deadline_val)
    if isinstance(deadline_val, str):
        deadline_str = deadline_val.strip()
        try:
            return float(deadline_str)
        except ValueError:
            pass
        try:
            clean_str = deadline_str.replace('Z', '+00:00')
            dt = datetime.datetime.fromisoformat(clean_str)
            return round(dt.timestamp(), 2)
        except Exception:
            pass
    raise ValueError("Invalid deadline format")


def create_job(data):
    # Support both backend snake_case and frontend camelCase field names
    job_id = str(data.get("id") or f"JOB-{int(time.time() * 1000)}").strip()
    tenant_id = str(data.get("tenant_id") or data.get("tenantId") or "").strip()
    raw_priority = str(data.get("priority") or "normal").strip().lower()

    raw_runtime = data.get("runtime_estimate") if "runtime_estimate" in data else data.get("runtime")
    raw_deadline = data.get("deadline")
    raw_capacity = data.get("required_capacity") if "required_capacity" in data else data.get("requiredCapacity")

    if not tenant_id:
        return None, {"error": "tenant_id or tenantId is required and cannot be blank"}, 400

    if raw_priority not in VALID_PRIORITIES:
        return None, {"error": f"Invalid priority. Must be one of {VALID_PRIORITIES}"}, 400

    try:
        runtime = float(raw_runtime)
        capacity = float(raw_capacity if raw_capacity is not None else 1)
        deadline = _parse_deadline(raw_deadline)
    except (TypeError, ValueError) as e:
        return None, {"error": f"Invalid numeric input: {str(e)}"}, 400

    if runtime <= 0 or capacity <= 0 or deadline < 0:
        return None, {"error": "runtime_estimate and required_capacity must be > 0, deadline must be >= 0"}, 400

    existing = db.get_job(job_id)
    if existing:
        return None, {"error": f"Job with id '{job_id}' already exists"}, 409

    job_payload = {
        "id": job_id,
        "tenant_id": tenant_id,
        "priority": raw_priority,
        "runtime_estimate": runtime,
        "deadline": deadline,
        "required_capacity": capacity,
        "status": "queued",
        "submitted_at": float(data.get("submitted_at", round(time.time(), 2)))
    }

    try:
        created = db.create_job(job_payload)
        db.log_event(job_id=job_id, worker_id=None, event_type="job_submitted", sim_time=job_payload["submitted_at"], details={"priority": raw_priority})
        return created, None, 201
    except Exception as e:
        return None, {"error": f"Failed to persist job: {str(e)}"}, 500


def get_all_jobs(status=None):
    if status and isinstance(status, str):
        status = status.strip().lower()
        if status == "all":
            status = None
    return db.get_jobs(status=status)



def get_job_by_id(job_id):
    job = db.get_job(job_id)
    if not job:
        return None, {"error": f"Job '{job_id}' not found"}, 404
    return job, None, 200
