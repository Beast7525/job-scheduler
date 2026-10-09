import os
import json
import time
import threading
from dotenv import load_dotenv
from database import get_db, init_db

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_lock = threading.Lock()

def _safe_supabase_call(fn, retries=3, initial_delay=0.05):
    """
    Executes a Supabase request with a thread lock and automatic retries
    for non-blocking socket errors ([WinError 10035]) or transient network issues.
    """
    with _supabase_lock:
        last_exception = None
        for attempt in range(retries):
            try:
                return fn()
            except Exception as e:
                last_exception = e
                err_msg = str(e)
                # Check for Windows non-blocking socket error (10035 / WSAEWOULDBLOCK) or transient network glitches
                is_transient = any(term in err_msg for term in ("10035", "WSAEWOULDBLOCK", "ReadError", "ConnectError", "Timeout", "transport error"))
                if is_transient and attempt < retries - 1:
                    time.sleep(initial_delay * (2 ** attempt))
                    continue
                raise e
        if last_exception:
            raise last_exception

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}")

# Always initialize SQLite database schema locally
init_db()

class DBWrapper:
    """
    Unified database client wrapper supporting both Supabase and SQLite.
    If Supabase is initialized and tables are valid, reads/writes go to Supabase.
    Otherwise, reads/writes fall back seamlessly to SQLite.
    """
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

    def is_supabase_enabled(self):
        return self.supabase is not None

    def get_jobs(self, status=None):
        if self.is_supabase_enabled():
            try:
                def _call():
                    query = self.supabase.table("jobs").select("*")
                    if status:
                        query = query.eq("status", status)
                    query = query.order("deadline")
                    return query.execute()

                res = _safe_supabase_call(_call)
                if res.data and isinstance(res.data, list) and len(res.data) > 0:
                    return res.data
            except Exception as e:
                print(f"Supabase query error: {e}, falling back to SQLite")
        
        with get_db() as conn:
            if status:
                rows = conn.execute("SELECT * FROM jobs WHERE status = ? ORDER BY deadline", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM jobs ORDER BY deadline").fetchall()
            return [dict(row) for row in rows]

    def get_job(self, job_id):
        if self.is_supabase_enabled():
            try:
                res = _safe_supabase_call(lambda: self.supabase.table("jobs").select("*").eq("id", str(job_id)).limit(1).execute())
                rows = res.data or []
                if rows and len(rows) > 0:
                    return rows[0]
            except Exception as e:
                print(f"Supabase query error: {e}, falling back to SQLite")
        
        with get_db() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (str(job_id),)).fetchone()
            return dict(row) if row else None

    def create_job(self, job_data):
        if self.is_supabase_enabled():
            try:
                res = _safe_supabase_call(lambda: self.supabase.table("jobs").insert(job_data).execute())
                if res.data and isinstance(res.data, list) and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                print(f"Supabase insert error: {e}, writing to SQLite")

        fields = list(job_data.keys())
        placeholders = ", ".join(["?"] * len(fields))
        columns = ", ".join(fields)
        values = [job_data[f] for f in fields]
        sql = f"INSERT INTO jobs ({columns}) VALUES ({placeholders})"
        with get_db() as conn:
            conn.execute(sql, values)
            conn.commit()
        return self.get_job(job_data["id"])

    def update_job(self, job_id, updates):
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("jobs").update(updates).eq("id", str(job_id)).execute())
            except Exception as e:
                print(f"Supabase update error: {e}, updating SQLite")

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [str(job_id)]
        sql = f"UPDATE jobs SET {set_clause} WHERE id = ?"
        with get_db() as conn:
            conn.execute(sql, values)
            conn.commit()

    def get_workers(self):
        if self.is_supabase_enabled():
            try:
                res = _safe_supabase_call(lambda: self.supabase.table("workers").select("*").order("id").execute())
                # Check if data returned has required columns for our schema
                if res.data and isinstance(res.data, list) and len(res.data) > 0 and "name" in res.data[0]:
                    return res.data
            except Exception as e:
                print(f"Supabase query error: {e}, falling back to SQLite")

        with get_db() as conn:
            rows = conn.execute("SELECT * FROM workers ORDER BY id").fetchall()
            return [dict(row) for row in rows]

    def get_worker(self, worker_id):
        if self.is_supabase_enabled():
            try:
                res = _safe_supabase_call(lambda: self.supabase.table("workers").select("*").eq("id", str(worker_id)).limit(1).execute())
                rows = res.data or []
                if rows and len(rows) > 0 and "name" in rows[0]:
                    return rows[0]
            except Exception as e:
                print(f"Supabase query error: {e}, falling back to SQLite")

        with get_db() as conn:
            row = conn.execute("SELECT * FROM workers WHERE id = ?", (str(worker_id),)).fetchone()
            return dict(row) if row else None

    def upsert_workers(self, worker_list):
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("workers").upsert(worker_list).execute())
            except Exception as e:
                print(f"Supabase upsert error: {e}, writing to SQLite")

        with get_db() as conn:
            for w in worker_list:
                name = w.get("name", f"Worker {w['id']}")
                conn.execute("""
                    INSERT INTO workers (id, name, capacity, available_at, status)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        capacity = excluded.capacity,
                        available_at = excluded.available_at,
                        status = excluded.status
                """, (w["id"], name, w["capacity"], w.get("available_at", 0), w.get("status", "online")))
            conn.commit()

    def update_worker(self, worker_id, updates):
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("workers").update(updates).eq("id", str(worker_id)).execute())
            except Exception as e:
                print(f"Supabase worker update error: {e}, updating SQLite")

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [str(worker_id)]
        sql = f"UPDATE workers SET {set_clause} WHERE id = ?"
        with get_db() as conn:
            conn.execute(sql, values)
            conn.commit()

    def log_event(self, job_id, worker_id, event_type, sim_time=0, details=None):
        details_str = json.dumps(details or {})
        log_payload = {
            "job_id": job_id,
            "worker_id": worker_id,
            "event_type": event_type,
            "simulation_time": sim_time,
            "details": details if self.is_supabase_enabled() else details_str
        }
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("execution_logs").insert(log_payload).execute())
            except Exception as e:
                print(f"Supabase log error: {e}")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO execution_logs (job_id, worker_id, event_type, simulation_time, details)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, worker_id, event_type, sim_time, details_str))
            conn.commit()

    def record_scheduling_run(self, run_data):
        result_details = json.dumps(run_data.get("result", {}))
        payload = {
            "algorithm_name": run_data.get("algorithm_name", "priority_slack"),
            "simulation_time": run_data.get("simulation_time", 0),
            "planning_duration_ms": run_data.get("planning_duration_ms", 0),
            "deadline_met_count": run_data.get("deadline_met_count", 0),
            "deadline_missed_count": run_data.get("deadline_missed_count", 0),
            "utilization": run_data.get("utilization", 0.0),
            "fairness_score": run_data.get("fairness_score", 0.0),
            "capacity_violations": run_data.get("capacity_violations", 0),
            "result": run_data.get("result", {}) if self.is_supabase_enabled() else result_details
        }
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("scheduling_runs").insert(payload).execute())
            except Exception as e:
                print(f"Supabase scheduling run log error: {e}")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO scheduling_runs (
                    algorithm_name, simulation_time, planning_duration_ms,
                    deadline_met_count, deadline_missed_count, utilization,
                    fairness_score, capacity_violations, result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                payload["algorithm_name"], payload["simulation_time"], payload["planning_duration_ms"],
                payload["deadline_met_count"], payload["deadline_missed_count"], payload["utilization"],
                payload["fairness_score"], payload["capacity_violations"], result_details
            ))
            conn.commit()

    def reset_all(self):
        """Reset database state to clean default for repeatable demo runs."""
        if self.is_supabase_enabled():
            try:
                _safe_supabase_call(lambda: self.supabase.table("execution_logs").delete().neq("id", 0).execute())
                _safe_supabase_call(lambda: self.supabase.table("scheduling_runs").delete().neq("id", 0).execute())
                _safe_supabase_call(lambda: self.supabase.table("jobs").delete().neq("id", "none").execute())
                _safe_supabase_call(lambda: self.supabase.table("workers").delete().neq("id", "none").execute())
            except Exception as e:
                print(f"Supabase reset error: {e}")

        with get_db() as conn:
            conn.execute("DELETE FROM execution_logs;")
            conn.execute("DELETE FROM scheduling_runs;")
            conn.execute("DELETE FROM jobs;")
            conn.execute("DELETE FROM workers;")
            conn.commit()

db = DBWrapper(supabase)

