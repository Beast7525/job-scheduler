# D05 — Deadline-Aware Compute Resource Optimizer
## Member 3: Backend, Supabase Database, and Worker Simulation

**Project:** Deadline-Aware Compute Resource Optimizer (D05)  
**Module owner:** Team Member 3  
**Backend:** Python + Flask  
**Database:** Supabase PostgreSQL  
**Shared scheduler contract:** Member 2's job and worker JSON formats  
**Purpose:** Provide API endpoints, persistent state, worker simulation, execution tracking, capacity enforcement, failure/recovery controls, and integration with the scheduler and frontend.

---

## 1. Your responsibilities

As Member 3, you own the backend infrastructure:

- Build the Flask REST API.
- Connect Flask to Supabase PostgreSQL.
- Store jobs, workers, execution events, and scheduling-run metrics.
- Implement worker initialization and worker-state APIs.
- Implement job submission and status retrieval.
- Simulate job execution and track start/finish outcomes.
- Enforce the agreed one-job-at-a-time worker rule.
- Handle worker capacity changes, failures, and recovery.
- Call Member 2's scheduler through a stable interface.
- Provide predictable API responses for Member 1's dashboard.
- Test validation, capacity safety, state transitions, and recovery.

### Team responsibilities

| Member | Responsibility |
|---|---|
| Member 1 | React dashboard, forms, job/worker tables, timeline, metrics visualizations |
| Member 2 | Scheduling algorithm, deadline feasibility, assignment decisions, live replanning, baseline comparison |
| **Member 3 (you)** | Flask API, Supabase, worker simulation, execution state, capacity enforcement, failure/recovery endpoints, integration |

Agree on field names, IDs, time units, and endpoint response formats with Members 1 and 2 before integration.

---

## 2. Architecture and workflow

```text
React dashboard (Member 1)
          |
          v
      Flask API
          |
          +------ Supabase PostgreSQL
          |       jobs
          |       workers
          |       execution_logs
          |       scheduling_runs
          |
          +------ Worker simulation (Member 3)
          |
          +------ Scheduler interface (Member 2)
                         |
                         v
                  Proposed schedule
```

Typical workflow:

1. The frontend submits a job to Flask.
2. Flask validates it and inserts it into Supabase with status `queued`.
3. Flask reads queued jobs and online workers from Supabase.
4. The backend passes data in the shared format to Member 2's scheduler.
5. The scheduler returns proposed assignments and predicted finish times.
6. The backend validates the assignments against worker availability and capacity.
7. Eligible jobs are started by the worker simulator.
8. Job completion updates the job, worker availability, and execution log.
9. An urgent job, worker failure, recovery, or capacity change triggers replanning.
10. The dashboard reads jobs, workers, and metrics through the API.

**MVP policy:** Each worker runs one job at a time. New urgent jobs do not preempt already-running jobs; the scheduler replans queued jobs. For the first version, a failed/offline worker does not accept new jobs. Coordinate with the team whether running jobs continue in simulation or are interrupted; choose one policy and implement it consistently.

---

## 3. Shared input format from Member 2

The scheduler/backend boundary must use the following field names. Supabase can store these same fields, which avoids unnecessary conversions.

### Job object

```json
{
  "id": "J101",
  "tenant_id": "Team-A",
  "priority": "critical",
  "runtime_estimate": 5,
  "deadline": 20,
  "required_capacity": 1,
  "status": "queued"
}
```

### Worker object

```json
{
  "id": "W1",
  "capacity": 2,
  "available_at": 0,
  "status": "online"
}
```

### Field definitions

| Field | Meaning |
|---|---|
| `id` | Stable string ID, e.g. `J101` for a job or `W1` for a worker |
| `tenant_id` | Team or tenant that submitted the job |
| `priority` | `critical`, `high`, `normal`, or `low` |
| `runtime_estimate` | Predicted execution duration in seconds |
| `deadline` | Absolute deadline on the simulation clock, in seconds |
| `required_capacity` | Compute capacity needed by a job while it runs |
| `status` | Job state, initially `queued` |
| `capacity` | Maximum compute capacity available on a worker |
| `available_at` | Earliest simulation-clock time the worker can accept its next job |
| Worker `status` | `online` or `offline` |

### Scheduling rules

- A worker may run **only one job at a time**.
- `capacity` represents compute capacity, not the number of concurrent jobs.
- Assign a job only if `job.required_capacity <= worker.capacity`.
- An offline worker must not receive new jobs.
- A job cannot start before `worker.available_at`.
- Predicted finish time is `start_time + runtime_estimate`.
- After assigning a job, the worker's next `available_at` is the job's predicted finish time.
- All simulation times must use the same units: seconds.
- Do not compare wall-clock timestamps with simulation-relative deadlines.

---

## 4. Project structure

```text
project/
├── frontend/                       # Member 1
└── backend/                        # Member 3
    ├── app.py
    ├── db.py
    ├── scheduler_adapter.py
    ├── requirements.txt
    ├── .env                        # local secrets; never commit
    ├── .gitignore
    ├── routes/
    │   ├── __init__.py
    │   ├── jobs.py
    │   ├── workers.py
    │   ├── simulation.py
    │   └── metrics.py
    ├── services/
    │   ├── __init__.py
    │   ├── job_service.py
    │   ├── worker_service.py
    │   └── execution_service.py
    └── tests/
        ├── test_jobs.py
        ├── test_workers.py
        └── test_simulation.py
```

Keep route handlers focused on request validation and HTTP responses. Put database and state-transition logic in service functions. The scheduler adapter is the boundary between Member 2's algorithm and your backend.

---

## 5. Set up Flask and Supabase

### Step 1 — Create a Supabase project

1. Create a project at [Supabase](https://supabase.com/).
2. Open the project's API settings.
3. Copy the project URL and a server-side secret/service-role key.
4. Put them in your backend `.env` file.
5. Never expose the server-side key in React, screenshots, public repositories, or frontend environment variables.

Create `backend/.env`:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_KEY=YOUR_SERVER_SIDE_SECRET_KEY
```

Create `backend/.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
```

### Step 2 — Create a virtual environment

From the `backend/` directory:

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install packages:

```bash
pip install Flask Flask-Cors supabase python-dotenv
pip freeze > requirements.txt
```

### Step 3 — Create `db.py`

```python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError(
        "Set SUPABASE_URL and SUPABASE_KEY in backend/.env"
    )

supabase: Client = create_client(url, key)
```

The server-side key should be used only by Flask. For the MVP, route database reads and writes through Flask so the backend remains responsible for validating assignments and enforcing capacity.

---

## 6. Create the Supabase database schema

In Supabase, open **SQL Editor**, create a new query, and run:

```sql
create table if not exists public.jobs (
  id text primary key,
  tenant_id text not null,
  priority text not null default 'normal'
    check (priority in ('critical', 'high', 'normal', 'low')),
  runtime_estimate integer not null check (runtime_estimate > 0),
  deadline integer not null check (deadline >= 0),
  required_capacity integer not null default 1
    check (required_capacity > 0),
  status text not null default 'queued'
    check (status in (
      'queued', 'scheduled', 'running',
      'completed', 'failed', 'interrupted', 'cancelled'
    )),
  assigned_worker_id text,
  available_at integer,
  submitted_at integer not null default 0,
  start_time integer,
  finish_time integer,
  deadline_met boolean,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.workers (
  id text primary key,
  capacity integer not null check (capacity > 0),
  available_at integer not null default 0,
  status text not null default 'online'
    check (status in ('online', 'offline')),
  current_job_id text references public.jobs(id) on delete set null,
  updated_at timestamptz not null default now()
);

alter table public.jobs
  add constraint jobs_assigned_worker_fk
  foreign key (assigned_worker_id)
  references public.workers(id)
  on delete set null;

create table if not exists public.execution_logs (
  id bigint generated by default as identity primary key,
  job_id text references public.jobs(id) on delete set null,
  worker_id text references public.workers(id) on delete set null,
  event_type text not null,
  simulation_time integer not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.scheduling_runs (
  id bigint generated by default as identity primary key,
  algorithm_name text not null,
  simulation_time integer not null default 0,
  planning_duration_ms numeric,
  deadline_met_count integer not null default 0,
  deadline_missed_count integer not null default 0,
  utilization numeric,
  fairness_score numeric,
  capacity_violations integer not null default 0,
  result jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists jobs_status_deadline_idx
  on public.jobs (status, deadline);

create index if not exists logs_job_id_idx
  on public.execution_logs (job_id);

create index if not exists logs_simulation_time_idx
  on public.execution_logs (simulation_time);
```

The IDs are text so the database can preserve `J101` and `W1`. This schema is intended for the project MVP. If you already ran an earlier schema, check existing constraints before rerunning the `ALTER TABLE` statement.

### What each table stores

| Table | Purpose |
|---|---|
| `jobs` | Job input, current status, assignment, predicted/actual times, deadline outcome |
| `workers` | Worker capacity, next available simulation time, online/offline state |
| `execution_logs` | Job submissions, starts, completions, failures, worker events |
| `scheduling_runs` | Planning duration, algorithm name, metrics, and plan output |

**Time rule:** `runtime_estimate`, `deadline`, `available_at`, `start_time`, `finish_time`, and `simulation_time` are simulation-clock seconds. Keep them consistent across frontend, backend, and scheduler.

---

## 7. Initialize Flask and check health

Create `app.py`:

```python
from flask import Flask, jsonify
from flask_cors import CORS

from routes.jobs import jobs_bp
from routes.workers import workers_bp
from routes.simulation import simulation_bp
from routes.metrics import metrics_bp

app = Flask(__name__)
CORS(app)  # Restrict allowed origins before any production deployment.

app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
app.register_blueprint(workers_bp, url_prefix="/api/workers")
app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
app.register_blueprint(metrics_bp, url_prefix="/api/metrics")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "deadline-aware-compute-optimizer"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
```

Create empty `__init__.py` files in `routes/` and `services/`. Add each route module before starting the full app, or temporarily register only the routes you have created.

Start the server:

```bash
python app.py
```

Open `http://127.0.0.1:5000/api/health`. Expected response:

```json
{
  "status": "ok",
  "service": "deadline-aware-compute-optimizer"
}
```

---

## 8. Worker initialization and retrieval

Create three workers with IDs `W1`, `W2`, and `W3`, each with capacity `2` and `available_at = 0`.

Example service function:

```python
from db import supabase

DEFAULT_WORKERS = [
    {"id": "W1", "capacity": 2, "available_at": 0, "status": "online"},
    {"id": "W2", "capacity": 2, "available_at": 0, "status": "online"},
    {"id": "W3", "capacity": 2, "available_at": 0, "status": "online"},
]


def initialize_workers():
    existing = supabase.table("workers").select("id").execute().data or []
    existing_ids = {worker["id"] for worker in existing}
    missing = [w for w in DEFAULT_WORKERS if w["id"] not in existing_ids]

    if missing:
        supabase.table("workers").insert(missing).execute()

    return supabase.table("workers").select("*").order("id").execute().data


def list_workers():
    response = supabase.table("workers").select("*").order("id").execute()
    return response.data or []
```

Do not blindly overwrite existing worker state during initialization; jobs may already be running. Use a dedicated reset operation for a clean demo.

Worker eligibility:
- `status` must be `online`.
- `job.required_capacity <= worker.capacity`.
- `worker.available_at <= proposed_start_time`.
- The worker must not already have an active job at that time.

---

## 9. Job API

Implement these endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/jobs/` | Validate and create a queued job |
| `GET` | `/api/jobs/` | List jobs |
| `GET` | `/api/jobs/<job_id>` | Retrieve one job |

### Example submission body

```json
{
  "id": "J101",
  "tenant_id": "Team-A",
  "priority": "critical",
  "runtime_estimate": 5,
  "deadline": 20,
  "required_capacity": 1,
  "status": "queued"
}
```

### Example route

Create `routes/jobs.py`:

```python
from flask import Blueprint, jsonify, request
from db import supabase

jobs_bp = Blueprint("jobs", __name__)

VALID_PRIORITIES = {"critical", "high", "normal", "low"}


@jobs_bp.post("/")
def create_job():
    data = request.get_json(silent=True) or {}

    required = {
        "id", "tenant_id", "priority",
        "runtime_estimate", "deadline", "required_capacity"
    }
    missing = sorted(required - data.keys())
    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing
        }), 400

    job_id = str(data["id"]).strip()
    tenant_id = str(data["tenant_id"]).strip()
    priority = str(data["priority"]).lower()

    try:
        runtime = int(data["runtime_estimate"])
        deadline = int(data["deadline"])
        capacity = int(data["required_capacity"])
    except (TypeError, ValueError):
        return jsonify({"error": "Runtime, deadline, and capacity must be integers"}), 400

    if not job_id or not tenant_id:
        return jsonify({"error": "id and tenant_id cannot be blank"}), 400
    if priority not in VALID_PRIORITIES:
        return jsonify({"error": "Invalid priority"}), 400
    if runtime <= 0 or capacity <= 0 or deadline < 0:
        return jsonify({"error": "Invalid runtime, deadline, or required_capacity"}), 400

    payload = {
        "id": job_id,
        "tenant_id": tenant_id,
        "priority": priority,
        "runtime_estimate": runtime,
        "deadline": deadline,
        "required_capacity": capacity,
        "status": "queued",
        "submitted_at": 0
    }

    try:
        result = supabase.table("jobs").insert(payload).execute()
        job = result.data[0]

        supabase.table("execution_logs").insert({
            "job_id": job_id,
            "event_type": "job_submitted",
            "simulation_time": 0,
            "details": {"priority": priority}
        }).execute()

        return jsonify(job), 201
    except Exception:
        # In a real app, log the exception on the server without exposing secrets.
        return jsonify({"error": "Could not create job; check ID uniqueness and database settings"}), 409


@jobs_bp.get("/")
def get_jobs():
    try:
        result = (
            supabase.table("jobs")
            .select("*")
            .order("deadline")
            .execute()
        )
        return jsonify({"jobs": result.data or []})
    except Exception:
        return jsonify({"error": "Could not retrieve jobs"}), 500


@jobs_bp.get("/<job_id>")
def get_job(job_id):
    try:
        result = (
            supabase.table("jobs")
            .select("*")
            .eq("id", job_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(rows[0])
    except Exception:
        return jsonify({"error": "Could not retrieve job"}), 500
```

For a production service, catch and log specific Supabase exceptions rather than returning a generic error for every failure. Never return secret keys or raw internal exception details to the client.

---

## 10. Execution lifecycle and capacity enforcement

Implement execution logic in `services/execution_service.py`, not directly in a Flask route.

For each proposed assignment:

1. Confirm the job is `queued` or otherwise eligible.
2. Confirm the worker is online.
3. Confirm `required_capacity <= capacity`.
4. Confirm the worker is free at the proposed start time.
5. Reserve the worker and update the job to `running`.
6. Record `start_time` and insert an execution log.
7. When simulated execution finishes, update `finish_time` and job status.
8. Compute `deadline_met = finish_time <= deadline`.
9. Set the worker's `available_at` to the finish time and clear its current job.
10. Insert a completion/failure log.

### Critical rules

- A worker can have no more than one running job.
- Capacity reservation and job status transition should be atomic.
- Completion must release the worker only once.
- Never mark a job completed before its simulated finish time.
- A failed start must not leave the worker reserved.
- Do not let two requests dispatch different jobs to the same worker concurrently.

**Supabase/PostgreSQL note:** Multiple independent REST requests are not an atomic transaction. For robust dispatch, implement a PostgreSQL function and call it through Supabase RPC so checking availability, reserving a worker, and changing the job state occur atomically. For a small demo, a single-threaded simulation loop can reduce race risks, but it is not a substitute for atomic transactions under concurrent requests.

For the simplest MVP, use a deterministic simulation tick loop instead of sleeping for the entire estimated runtime. The scheduler and backend must share the same simulation clock.

---

## 11. Worker failure, capacity changes, and recovery

Implement these endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/workers` | List worker states |
| `PATCH` | `/api/workers/<worker_id>/capacity` | Change worker capacity |
| `POST` | `/api/simulation/initialize` | Ensure default workers exist |
| `POST` | `/api/simulation/worker-failure` | Mark a worker offline |
| `POST` | `/api/simulation/worker-recovery` | Bring a worker online |
| `POST` | `/api/simulation/reset` | Reset the simulation for a repeatable demo |

Use request bodies such as:

```json
{"worker_id": "W2"}
```

for failure/recovery, and:

```json
{"capacity": 1}
```

for capacity changes.

When a worker fails:
- Mark it offline.
- Record a `worker_failed` log.
- Do not assign new jobs to it.
- Trigger replanning for queued jobs.
- Apply the agreed policy to any running job.

When a worker recovers:
- Mark it online.
- Preserve the correct `available_at` and active-job state.
- Record a `worker_recovered` log.
- Trigger replanning.

When capacity decreases, reject invalid values and do not alter the capacity assumptions for jobs already running without an explicit policy. In this MVP, capacity is a per-job eligibility limit and each worker runs one job at a time.

---

## 12. Integrate Member 2's scheduler

Use a stable adapter so the backend does not depend on the scheduler's internal implementation details.

Example contract:

```python
def create_schedule(jobs, workers, current_time):
    """
    jobs: list of shared-format job dictionaries
    workers: list of shared-format worker dictionaries
    current_time: integer simulation time in seconds

    Returns a plan with assignments and predicted finish times.
    """
    ...
```

The adapter should:

1. Fetch queued jobs from Supabase.
2. Fetch worker state from Supabase.
3. Pass dictionaries using the exact shared field names.
4. Call Member 2's scheduler.
5. Validate proposed assignments.
6. Persist the plan in `scheduling_runs` or an agreed plan table.
7. Dispatch eligible jobs through the execution service.
8. Return the plan to the frontend.

Suggested joint endpoints:

- `POST /api/scheduler/plan`
- `POST /api/scheduler/replan`

Trigger replanning when:
- A new urgent job arrives.
- A worker goes offline.
- A worker's capacity changes.
- A worker recovers.
- A running job completes and frees a worker.

The scheduler proposes assignments; the backend validates and applies them. Do not let both modules independently reserve workers.

---

## 13. Metrics and frontend API contract

Agree the exact metrics definitions with Members 1 and 2. Suggested metrics include:

- **Deadline compliance:** completed jobs that finished by their deadlines divided by completed jobs.
- **Worker utilization:** time workers spent executing jobs divided by available worker time in the measured simulation window.
- **Fairness:** use the team's agreed per-tenant or per-job waiting-time metric.
- **Planning overhead:** scheduler computation time, in milliseconds.
- **Capacity violations:** count of assignments rejected because the worker was offline, busy, or lacked capacity.

Suggested endpoints:

| Method | Endpoint | Owner/notes |
|---|---|---|
| `GET` | `/api/health` | Member 3 |
| `POST` | `/api/jobs/` | Member 3 |
| `GET` | `/api/jobs/` | Member 3 |
| `GET` | `/api/workers` | Member 3 |
| `POST` | `/api/simulation/initialize` | Member 3 |
| `POST` | `/api/simulation/worker-failure` | Member 3 |
| `POST` | `/api/simulation/worker-recovery` | Member 3 |
| `POST` | `/api/scheduler/plan` | Shared with Member 2 |
| `POST` | `/api/scheduler/replan` | Shared with Member 2 |
| `GET` | `/api/metrics` | Shared with Member 2 |

Use consistent JSON error responses, for example:

```json
{"error": "Worker not found"}
```

Use appropriate HTTP statuses such as `400` for invalid input, `404` for missing records, `409` for conflicts, and `500` for unexpected server errors.

---

## 14. Testing checklist

### Setup and database
- [ ] Flask health endpoint returns `200`.
- [ ] Flask can connect to Supabase.
- [ ] Default workers are inserted without overwriting existing state.
- [ ] Jobs and logs persist after the server restarts.
- [ ] `.env` is excluded from Git.

### Job API
- [ ] Valid job returns `201`.
- [ ] Duplicate job ID returns a conflict response.
- [ ] Missing fields are rejected.
- [ ] Invalid priority, runtime, deadline, and capacity are rejected.
- [ ] Job listing and single-job lookup work.

### Worker and execution
- [ ] Offline workers cannot receive jobs.
- [ ] A job requiring more capacity than the worker has is rejected for that worker.
- [ ] No worker is assigned overlapping jobs.
- [ ] Worker `available_at` updates to the predicted/actual finish time according to the simulation policy.
- [ ] Completion updates job state and logs the outcome.
- [ ] Deadline result is computed from actual simulated finish time.
- [ ] Duplicate completion cannot free a worker twice.

### Failure and integration
- [ ] Worker failure is recorded and blocks new assignments.
- [ ] Recovery restores eligibility without erasing active reservations.
- [ ] Capacity change triggers replanning.
- [ ] Urgent job submission triggers replanning.
- [ ] Scheduler output is validated before dispatch.
- [ ] The simulation can be reset and the demo repeated.

---

## 15. Seven-day development schedule

| Day | Deliverable |
|---|---|
| 1 | Create Supabase project, tables, Flask environment, `db.py`, health endpoint |
| 2 | Job submission/listing API and worker initialization/listing |
| 3 | Execution lifecycle, simulation clock, and worker availability updates |
| 4 | Failure, capacity change, recovery, and execution logs |
| 5 | Scheduler adapter and replanning integration with Member 2 |
| 6 | API tests, capacity edge cases, error handling, and frontend integration |
| 7 | Full demo, bug fixes, and repeatable reset scenario |

Recommended order: health check → Supabase connection → initialize workers → submit/list jobs → execute one job → failure/recovery → scheduler integration → frontend.

---

## 16. Judge demonstration scenario

1. Reset the simulation and initialize `W1`, `W2`, and `W3`.
2. Submit several jobs with different priorities, runtimes, and deadlines.
3. Generate a schedule and show the proposed assignments.
4. Start eligible jobs and show worker availability updates.
5. Submit a critical job with a near deadline.
6. Show that the backend records the job and requests replanning.
7. Take one worker offline or reduce its capacity.
8. Show that no invalid assignment is dispatched and the plan is recomputed.
9. Restore the worker and show it becomes eligible again.
10. Show Supabase rows for jobs, workers, execution logs, and scheduling runs.

A predicted deadline result is not the same as an actual result. Report a job as meeting its deadline only when its simulated finish time is at or before the deadline.

---

## 17. Definition of done

Your module is ready when:

- Flask runs and the health endpoint works.
- Flask reads and writes the shared Supabase project.
- IDs and field names match Member 2's scheduler contract.
- Job and worker APIs work with the agreed JSON shapes.
- The backend enforces one job per worker and capacity eligibility.
- Execution state transitions and logs are recorded consistently.
- Failure/recovery updates worker eligibility and triggers replanning.
- The frontend can view jobs, workers, and metrics.
- The team can reset and repeat the demo without stale state.
- No Supabase server-side secret is exposed to the frontend or committed to source control.
