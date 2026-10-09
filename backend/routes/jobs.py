from flask import Blueprint, jsonify, request
from services.job_service import create_job, get_all_jobs, get_job_by_id
from scheduler_adapter import create_schedule

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.post("/")
def submit_job():
    data = request.get_json(silent=True) or {}
    job, err, status_code = create_job(data)
    if err:
        return jsonify(err), status_code

    if job and job.get("priority") in ("critical", "high"):
        create_schedule()

    return jsonify(job), 201


@jobs_bp.get("/")
def list_jobs():
    status = request.args.get("status")
    jobs = get_all_jobs(status=status)
    return jsonify({"jobs": jobs})


@jobs_bp.get("/<job_id>")
def retrieve_job(job_id):
    job, err, status_code = get_job_by_id(job_id)
    if err:
        return jsonify(err), status_code
    return jsonify(job)
