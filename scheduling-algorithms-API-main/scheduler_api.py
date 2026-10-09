
from flask import Flask, request, jsonify
from scheduler.service import schedule_jobs
from scheduler.replanner import replan_queued_jobs

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Deadline-Aware Compute Resource Optimizer",
    })


@app.route("/schedule", methods=["POST"])
def schedule():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    jobs = data.get("jobs")
    workers = data.get("workers")
    policy = data.get("policy", "proposed")
    current_time = data.get("current_time", 0)

    if not isinstance(jobs, list) or not isinstance(workers, list):
        return jsonify({
            "error": "'jobs' and 'workers' must be arrays"
        }), 400
    
    # Validate scheduling policy.
    allowed_policies = {"proposed", "fifo", "edf", "tenant_fair"}

    if policy not in allowed_policies:
        return jsonify({
            "error": "Invalid policy",
            "allowed_policies": sorted(allowed_policies),
        }), 400

    # Validate simulation time.
    if (
        isinstance(current_time, bool)
        or not isinstance(current_time, (int, float))
        or current_time < 0
    ):
        return jsonify({
            "error": "current_time must be a non-negative number"
        }), 400

    # Validate jobs.
    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            return jsonify({
                "error": f"Job at index {index} must be an object"
            }), 400

        if not isinstance(job.get("id"), str) or not job["id"].strip():
            return jsonify({
                "error": f"Job at index {index} needs a non-empty string id"
            }), 400

        for field in ("runtime", "deadline", "required_capacity"):
            value = job.get(field)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                return jsonify({
                    "error": f"Job {job['id']}: {field} must be numeric"
                }), 400

        if job["runtime"] <= 0:
            return jsonify({
                "error": f"Job {job['id']}: runtime must be greater than zero"
            }), 400

        if job["required_capacity"] <= 0:
            return jsonify({
                "error": f"Job {job['id']}: required_capacity must be positive"
            }), 400

        if not isinstance(job.get("priority", "normal"), str):
            return jsonify({
                "error": f"Job {job['id']}: priority must be a string"
            }), 400

    # Validate workers.
    for index, worker in enumerate(workers):
        if not isinstance(worker, dict):
            return jsonify({
                "error": f"Worker at index {index} must be an object"
            }), 400

        if not isinstance(worker.get("id"), str) or not worker["id"].strip():
            return jsonify({
                "error": f"Worker at index {index} needs a non-empty string id"
            }), 400

        capacity = worker.get("capacity")
        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, (int, float))
            or capacity <= 0
        ):
            return jsonify({
                "error": f"Worker {worker['id']}: capacity must be positive"
            }), 400

        if not isinstance(worker.get("online", True), bool):
            return jsonify({
                "error": f"Worker {worker['id']}: online must be true or false"
            }), 400

    try:
        result = schedule_jobs(
            jobs=jobs,
            workers=workers,
            policy=policy,
            current_time=current_time,
        )
        return jsonify(result)

    except (ValueError, KeyError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

@app.route("/replan", methods=["POST"])
def replan():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    jobs = data.get("jobs")
    workers = data.get("workers")
    running_jobs = data.get("running_jobs", [])
    current_time = data.get("current_time", 0)

    if not isinstance(jobs, list) or not isinstance(workers, list):
        return jsonify({
            "error": "'jobs' and 'workers' must be arrays"
        }), 400

    if not isinstance(running_jobs, list):
        return jsonify({
            "error": "'running_jobs' must be an array"
        }), 400

    if (
        isinstance(current_time, bool)
        or not isinstance(current_time, (int, float))
        or current_time < 0
    ):
        return jsonify({
            "error": "current_time must be a non-negative number"
        }), 400

    worker_ids = set()

    for index, worker in enumerate(workers):
        if not isinstance(worker, dict):
            return jsonify({
                "error": f"Worker at index {index} must be an object"
            }), 400

        worker_id = worker.get("id")
        capacity = worker.get("capacity")

        if not isinstance(worker_id, str) or not worker_id.strip():
            return jsonify({
                "error": f"Worker at index {index} needs a non-empty string id"
            }), 400

        if worker_id in worker_ids:
            return jsonify({
                "error": f"Duplicate worker id: {worker_id}"
            }), 400

        if (
            isinstance(capacity, bool)
            or not isinstance(capacity, (int, float))
            or capacity <= 0
        ):
            return jsonify({
                "error": f"Worker {worker_id}: capacity must be positive"
            }), 400

        if not isinstance(worker.get("online", True), bool):
            return jsonify({
                "error": f"Worker {worker_id}: online must be true or false"
            }), 400

        worker_ids.add(worker_id)

    job_ids = set()

    for index, job in enumerate(jobs):
        if not isinstance(job, dict):
            return jsonify({
                "error": f"Job at index {index} must be an object"
            }), 400

        job_id = job.get("id")

        if not isinstance(job_id, str) or not job_id.strip():
            return jsonify({
                "error": f"Job at index {index} needs a non-empty string id"
            }), 400

        if job_id in job_ids:
            return jsonify({
                "error": f"Duplicate job id: {job_id}"
            }), 400

        job_ids.add(job_id)

        for field in ("runtime", "deadline", "required_capacity"):
            value = job.get(field)

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
            ):
                return jsonify({
                    "error": f"Job {job_id}: {field} must be numeric"
                }), 400

        if job["runtime"] <= 0:
            return jsonify({
                "error": f"Job {job_id}: runtime must be greater than zero"
            }), 400

        if job["required_capacity"] <= 0:
            return jsonify({
                "error": f"Job {job_id}: required_capacity must be positive"
            }), 400

    running_ids = set()

    for index, running in enumerate(running_jobs):
        if not isinstance(running, dict):
            return jsonify({
                "error": f"Running job at index {index} must be an object"
            }), 400

        job_id = running.get("job_id")
        worker_id = running.get("worker_id")
        finish_time = running.get("finish_time")

        if not isinstance(job_id, str) or job_id not in job_ids:
            return jsonify({
                "error": f"Running job at index {index} has an unknown job_id"
            }), 400

        if job_id in running_ids:
            return jsonify({
                "error": f"Duplicate running job: {job_id}"
            }), 400

        if worker_id not in worker_ids:
            return jsonify({
                "error": f"Running job {job_id} references an unknown worker"
            }), 400

        if (
            isinstance(finish_time, bool)
            or not isinstance(finish_time, (int, float))
            or finish_time < current_time
        ):
            return jsonify({
                "error": (
                    f"Running job {job_id}: finish_time must be "
                    "numeric and at least current_time"
                )
            }), 400

        running_ids.add(job_id)

    try:
        result = replan_queued_jobs(
            jobs=jobs,
            workers=workers,
            current_time=current_time,
            running_jobs=running_jobs,
        )
        return jsonify(result)

    except (ValueError, KeyError, TypeError) as error:
        return jsonify({"error": str(error)}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)