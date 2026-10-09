from routes.jobs import jobs_bp
from routes.workers import workers_bp
from routes.simulation import simulation_bp
from routes.scheduler import scheduler_bp
from routes.metrics import metrics_bp

__all__ = ["jobs_bp", "workers_bp", "simulation_bp", "scheduler_bp", "metrics_bp"]
