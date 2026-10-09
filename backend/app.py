import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from db import supabase, db, _safe_supabase_call
from database import init_db
from routes import jobs_bp, workers_bp, simulation_bp, scheduler_bp, metrics_bp

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

init_db()

app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
app.register_blueprint(workers_bp, url_prefix="/api/workers")
app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
app.register_blueprint(scheduler_bp, url_prefix="/api/scheduler")
app.register_blueprint(metrics_bp, url_prefix="/api/metrics")


@app.route('/')
def index():
    """Root route querying Supabase or local state."""
    todos = []
    if supabase is not None:
        try:
            response = _safe_supabase_call(lambda: supabase.table('todos').select("*").execute())
            todos = response.data or []
        except Exception:
            todos = []

    if todos:
        html = '<h1>Todos</h1><ul>'
        for todo in todos:
            name = todo.get("name", str(todo))
            html += f'<li>{name}</li>'
        html += '</ul>'
        return html

    return jsonify({
        "status": "ok",
        "service": "deadline-aware-compute-optimizer",
        "supabase_connected": db.is_supabase_enabled(),
        "endpoints": [
            "/api/health",
            "/api/jobs",
            "/api/workers",
            "/api/simulation",
            "/api/scheduler/plan",
            "/api/metrics"
        ]
    })


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "deadline-aware-compute-optimizer",
        "supabase_connected": db.is_supabase_enabled()
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
