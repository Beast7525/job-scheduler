from flask import Blueprint, jsonify, request
from services.worker_service import list_workers, get_worker_by_id, update_worker_capacity
from scheduler_adapter import create_schedule

workers_bp = Blueprint("workers", __name__)


@workers_bp.get("/")
def get_workers():
    workers = list_workers()
    return jsonify({"workers": workers})


@workers_bp.get("/<worker_id>")
def get_worker(worker_id):
    worker, err, status_code = get_worker_by_id(worker_id)
    if err:
        return jsonify(err), status_code
    return jsonify(worker)


@workers_bp.patch("/<worker_id>/capacity")
def set_capacity(worker_id):
    data = request.get_json(silent=True) or {}
    if "capacity" not in data:
        return jsonify({"error": "Missing 'capacity' field"}), 400

    worker, err, status_code = update_worker_capacity(worker_id, data["capacity"])
    if err:
        return jsonify(err), status_code

    create_schedule()
    return jsonify(worker)
