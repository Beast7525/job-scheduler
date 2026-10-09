from flask import Blueprint, jsonify
from services.execution_service import compute_metrics

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.get("/")
def get_metrics():
    metrics = compute_metrics()
    return jsonify(metrics)
