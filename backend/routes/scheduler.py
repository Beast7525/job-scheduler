from flask import Blueprint, jsonify, request
from scheduler_adapter import create_schedule

scheduler_bp = Blueprint("scheduler", __name__)


@scheduler_bp.route("/plan", methods=["GET", "POST"])
def plan():
    data = request.get_json(silent=True) or {}
    jobs = data.get("jobs")
    workers = data.get("workers")
    current_time = data.get("current_time")

    schedule_plan = create_schedule(jobs=jobs, workers=workers, current_time=current_time)
    return jsonify(schedule_plan)


@scheduler_bp.route("/replan", methods=["GET", "POST"])
def replan():
    schedule_plan = create_schedule()
    return jsonify(schedule_plan)
