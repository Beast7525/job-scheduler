
from database import get_db


def initialize_workers(count=3, capacity=2):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) FROM workers"
        ).fetchone()[0]

        if existing:
            return

        for i in range(1, count + 1):
            conn.execute(
                """
                INSERT INTO workers
                    (name, capacity, available_capacity, status)
                VALUES (?, ?, ?, 'online')
                """,
                (f"Worker {i}", capacity, capacity)
            )


def list_workers():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM workers ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
