from flask import Blueprint, jsonify, request
from services.worker_service import initialize_workers, set_worker_failure, set_worker_recovery, reset_simulation
from services.execution_service import get_current_simulation_time, advance_simulation_time, set_simulation_time
from scheduler_adapter import create_schedule

simulation_bp = Blueprint("simulation", __name__)


@simulation_bp.post("/initialize")
def init_sim():
    workers = initialize_workers()
    return jsonify({"workers": workers})


@simulation_bp.post("/worker-failure")
def worker_failure():
    data = request.get_json(silent=True) or {}
    worker_id = data.get("worker_id") or data.get("workerId")
    if not worker_id:
        return jsonify({"error": "Missing 'worker_id' or 'workerId' field"}), 400

    sim_time = get_current_simulation_time()
    worker, err, status_code = set_worker_failure(worker_id, sim_time=sim_time)
    if err:
        return jsonify(err), status_code

    plan = create_schedule()
    return jsonify({"worker": worker, "plan": plan})


@simulation_bp.post("/worker-recovery")
def worker_recovery():
    data = request.get_json(silent=True) or {}
    worker_id = data.get("worker_id") or data.get("workerId")
    if not worker_id:
        return jsonify({"error": "Missing 'worker_id' or 'workerId' field"}), 400

    sim_time = get_current_simulation_time()
    worker, err, status_code = set_worker_recovery(worker_id, sim_time=sim_time)
    if err:
        return jsonify(err), status_code

    plan = create_schedule()
    return jsonify({"worker": worker, "plan": plan})



@simulation_bp.post("/reset")
def reset():
    result = reset_simulation()
    set_simulation_time(0)
    return jsonify(result)


@simulation_bp.get("/clock")
def get_clock():
    return jsonify({"simulation_time": get_current_simulation_time()})


@simulation_bp.post("/tick")
def tick():
    data = request.get_json(silent=True) or {}
    delta = float(data.get("delta", 1))
    new_time = advance_simulation_time(delta)
    return jsonify({"simulation_time": new_time})
