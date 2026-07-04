from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from threading import RLock
import time
from typing import Any


class JobIntegrityError(ValueError):
    """Exception raised when a job signature validation fails."""
    pass


def calculate_job_signature(job_id: str, created_at: float, request_json: str, status: str, output_dir: str | None, secret: str) -> str:
    """Computes a HMAC-SHA256 signature for a job payload to verify its integrity."""
    output_dir_str = output_dir or ""
    message = f"{job_id}|{created_at}|{request_json}|{status}|{output_dir_str}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()



@dataclass
class OptimizerJob:
    id: str
    created_at: float
    request: dict[str, Any]
    status: str = "PENDING"
    progress: dict[str, Any] = field(default_factory=dict)
    best: dict[str, Any] | None = None
    output_dir: str | None = None
    error: str | None = None
    cancel_requested: bool = False
    summary: dict[str, Any] | None = None

    def public_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "request": self.request,
            "status": self.status,
            "progress": self.progress,
            "best": self.best,
            "output_dir": self.output_dir,
            "error": self.error,
            "cancel_requested": self.cancel_requested,
            "summary": self.summary,
        }

    def store_payload(self) -> dict[str, Any]:
        payload = self.public_payload()
        return payload

    @classmethod
    def from_store_payload(cls, payload: dict[str, Any], *, fail_active: bool = False) -> "OptimizerJob":
        status = str(payload.get("status", "FAILED"))
        error = payload.get("error")
        if fail_active and status in SQLiteOptimizerJobStore.ACTIVE_STATUSES:
            status = "FAILED"
            error = error or "Job interrupted by optimizer worker restart"
        return cls(
            id=str(payload["id"]),
            created_at=float(payload.get("created_at", time.time())),
            request=dict(payload.get("request") or {}),
            status=status,
            progress=dict(payload.get("progress") or {}),
            best=payload.get("best") if isinstance(payload.get("best"), dict) else None,
            output_dir=str(payload["output_dir"]) if payload.get("output_dir") else None,
            error=str(error) if error else None,
            cancel_requested=bool(payload.get("cancel_requested", False)),
            summary=payload.get("summary") if isinstance(payload.get("summary"), dict) else None,
        )


class SQLiteOptimizerJobStore:
    """Persistent optimizer job store and lightweight SQLite-backed queue.

    The web process only creates/reads/cancels jobs. A separate worker process can
    atomically claim PENDING jobs and execute them, so optimizer lifetimes are no
    longer tied to FastAPI request handling or in-memory thread state.
    """

    ACTIVE_STATUSES = {"PENDING", "IN_PROGRESS"}
    JSON_FIELDS = {"request", "progress", "best", "summary"}

    def __init__(self, *, max_jobs: int = 100, ttl_seconds: int | None = 24 * 60 * 60, storage_path: Path | None = None) -> None:
        from .paths import get_reports_dir
        default_path = get_reports_dir() / "local_optimizer" / "jobs.sqlite3"
        self._storage_path = Path(storage_path or default_path)
        self._max_jobs = max(1, int(max_jobs))
        self._ttl_seconds = ttl_seconds if ttl_seconds is None else max(1, int(ttl_seconds))
        self._lock = RLock()
        
        # Load HMAC secret for job signing
        self._hmac_secret = os.getenv("JOB_STORE_HMAC_SECRET")
        if not self._hmac_secret:
            is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
            if is_prod:
                raise ValueError("JOB_STORE_HMAC_SECRET environment variable is required in production.")
            else:
                self._hmac_secret = "dev_default_hmac_secret_key_change_me_in_prod"

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._maintenance()


    @property
    def storage_path(self) -> Path:
        return self._storage_path

    def add(self, job: OptimizerJob) -> None:
        with self._lock, self._connect() as conn:
            now = time.time()
            self._cleanup_locked(conn)
            request_json = _json_dump(job.request)
            signature = calculate_job_signature(
                job_id=job.id,
                created_at=job.created_at,
                request_json=request_json,
                status=job.status,
                output_dir=job.output_dir,
                secret=self._hmac_secret
            )
            conn.execute(
                """
                INSERT INTO optimizer_jobs (
                    id, created_at, request_json, status, progress_json, best_json,
                    output_dir, error, cancel_requested, summary_json, updated_at, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    float(job.created_at),
                    request_json,
                    str(job.status),
                    _json_dump(job.progress),
                    _json_dump(job.best),
                    job.output_dir,
                    job.error,
                    1 if job.cancel_requested else 0,
                    _json_dump(job.summary),
                    now,
                    signature
                ),
            )
            self._enforce_limit_locked(conn)

    def get(self, job_id: str) -> OptimizerJob | None:
        with self._lock, self._connect() as conn:
            self._cleanup_locked(conn)
            row = conn.execute("SELECT * FROM optimizer_jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row_to_job(row) if row is not None else None

    def update(self, job_id: str, **updates: Any) -> None:
        if not updates:
            return
        allowed = {
            "request": "request_json",
            "status": "status",
            "progress": "progress_json",
            "best": "best_json",
            "output_dir": "output_dir",
            "error": "error",
            "cancel_requested": "cancel_requested",
            "summary": "summary_json",
        }

        with self._lock, self._connect() as conn:
            self._cleanup_locked(conn)
            row = conn.execute("SELECT * FROM optimizer_jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
                
            self._verify_job_signature(row)
            
            request_json = row["request_json"]
            status = row["status"]
            output_dir = row["output_dir"]
            created_at = row["created_at"]
            
            if "request" in updates:
                request_json = _json_dump(updates["request"])
            if "status" in updates:
                status = str(updates["status"])
            if "output_dir" in updates:
                output_dir = str(updates["output_dir"]) if updates["output_dir"] else None
                
            new_signature = calculate_job_signature(
                job_id=job_id,
                created_at=created_at,
                request_json=request_json,
                status=status,
                output_dir=output_dir,
                secret=self._hmac_secret
            )

            assignments: list[str] = []
            values: list[Any] = []
            for key, value in updates.items():
                if key not in allowed:
                    raise ValueError(f"Unsupported OptimizerJob update field: {key}")
                assignments.append(f"{allowed[key]} = ?")
                if key in self.JSON_FIELDS:
                    values.append(_json_dump(value))
                elif key == "cancel_requested":
                    values.append(1 if value else 0)
                else:
                    values.append(deepcopy(value))
            
            assignments.append("signature = ?")
            values.append(new_signature)
            assignments.append("updated_at = ?")
            values.append(time.time())
            values.append(job_id)

            cursor = conn.execute(f"UPDATE optimizer_jobs SET {', '.join(assignments)} WHERE id = ?", values)
            if cursor.rowcount == 0:
                raise KeyError(job_id)

    def delete(self, job_id: str) -> OptimizerJob | None:
        """Delete a job from the persistent store and return its last payload."""

        with self._lock, self._connect() as conn:
            self._cleanup_locked(conn)
            row = conn.execute("SELECT * FROM optimizer_jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            job = self._row_to_job(row)
            conn.execute("DELETE FROM optimizer_jobs WHERE id = ?", (job_id,))
            return job

    def list(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            self._cleanup_locked(conn)
            rows = conn.execute("SELECT * FROM optimizer_jobs ORDER BY created_at DESC").fetchall()
            return [self._row_to_job(row).public_payload() for row in rows]

    def claim_next(self, *, worker_id: str, now: float | None = None) -> OptimizerJob | None:
        """Atomically claim the oldest pending job for a worker process."""

        claimed_at = time.time() if now is None else float(now)
        with self._lock, self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._cleanup_locked(conn)
            row = conn.execute(
                "SELECT * FROM optimizer_jobs WHERE status = 'PENDING' ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            if row is None:
                conn.commit()
                return None
                
            self._verify_job_signature(row)
            
            new_sig = calculate_job_signature(
                job_id=row["id"],
                created_at=row["created_at"],
                request_json=row["request_json"],
                status="IN_PROGRESS",
                output_dir=row["output_dir"],
                secret=self._hmac_secret
            )
            
            conn.execute(
                """
                UPDATE optimizer_jobs
                SET status = 'IN_PROGRESS', worker_id = ?, locked_at = ?, updated_at = ?, signature = ?
                WHERE id = ?
                """,
                (worker_id, claimed_at, claimed_at, new_sig, row["id"]),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM optimizer_jobs WHERE id = ?", (row["id"],)).fetchone()
            return self._row_to_job(updated) if updated is not None else None

    def mark_interrupted_jobs_failed(self) -> None:
        with self._lock, self._connect() as conn:
            now = time.time()
            rows = conn.execute("SELECT * FROM optimizer_jobs WHERE status = 'IN_PROGRESS'").fetchall()
            for row in rows:
                try:
                    self._verify_job_signature(row)
                except JobIntegrityError:
                    pass
                new_sig = calculate_job_signature(
                    job_id=row["id"],
                    created_at=row["created_at"],
                    request_json=row["request_json"],
                    status="FAILED",
                    output_dir=row["output_dir"],
                    secret=self._hmac_secret
                )
                conn.execute(
                    """
                    UPDATE optimizer_jobs
                    SET status = 'FAILED',
                        error = COALESCE(error, 'Job interrupted by optimizer worker restart'),
                        updated_at = ?,
                        signature = ?
                    WHERE id = ?
                    """,
                    (now, new_sig, row["id"]),
                )

    def mark_worker_crashed(self, worker_id: str, error_message: str) -> int:
        with self._lock, self._connect() as conn:
            now = time.time()
            rows = conn.execute("SELECT * FROM optimizer_jobs WHERE status = 'IN_PROGRESS' AND worker_id = ?", (worker_id,)).fetchall()
            count = 0
            for row in rows:
                try:
                    self._verify_job_signature(row)
                except JobIntegrityError:
                    pass
                new_sig = calculate_job_signature(
                    job_id=row["id"],
                    created_at=row["created_at"],
                    request_json=row["request_json"],
                    status="FAILED",
                    output_dir=row["output_dir"],
                    secret=self._hmac_secret
                )
                conn.execute(
                    """
                    UPDATE optimizer_jobs
                    SET status = 'FAILED',
                        error = ?,
                        updated_at = ?,
                        signature = ?
                    WHERE id = ?
                    """,
                    (error_message, now, new_sig, row["id"]),
                )
                count += 1
            return count


    def _maintenance(self) -> None:
        with self._lock, self._connect() as conn:
            self._cleanup_locked(conn)
            self._enforce_limit_locked(conn)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS optimizer_jobs (
                    id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    request_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_json TEXT NOT NULL DEFAULT '{}',
                    best_json TEXT,
                    output_dir TEXT,
                    error TEXT,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    summary_json TEXT,
                    updated_at REAL NOT NULL,
                    worker_id TEXT,
                    locked_at REAL
                )
                """
            )
            try:
                conn.execute("ALTER TABLE optimizer_jobs ADD COLUMN signature TEXT")
            except sqlite3.OperationalError:
                pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_optimizer_jobs_status_created ON optimizer_jobs(status, created_at)")

    def _connect(self) -> sqlite3.Connection:
        encryption_key = os.getenv("SQLITE_ENCRYPTION_KEY")
        use_sqlcipher = False
        
        if encryption_key:
            try:
                from sqlcipher3 import dbapi2 as sqlcipher
                use_sqlcipher = True
            except ImportError:
                is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
                if is_prod:
                    raise ImportError("SQLCipher is required in production when SQLITE_ENCRYPTION_KEY is configured, but 'sqlcipher3' package is not installed.")
                else:
                    import logging
                    logging.getLogger("job_store").warning("[SECURITY WARNING] SQLITE_ENCRYPTION_KEY is set but sqlcipher3 is not installed. Falling back to unencrypted sqlite3.")

        if use_sqlcipher:
            from sqlcipher3 import dbapi2 as sqlcipher_db
            conn = sqlcipher_db.connect(self._storage_path, timeout=30.0, isolation_level=None)
        else:
            conn = sqlite3.connect(self._storage_path, timeout=30.0, isolation_level=None)
            
        conn.row_factory = sqlite3.Row
        
        if use_sqlcipher and encryption_key:
            conn.execute(f"PRAGMA key = '{encryption_key}'")

        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA secure_delete=ON")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    def _cleanup_locked(self, conn: sqlite3.Connection) -> None:
        if self._ttl_seconds is None:
            return
        cutoff = time.time() - self._ttl_seconds
        placeholders = ", ".join("?" for _ in self.ACTIVE_STATUSES)
        conn.execute(
            f"DELETE FROM optimizer_jobs WHERE created_at < ? AND status NOT IN ({placeholders})",
            (cutoff, *self.ACTIVE_STATUSES),
        )

    def _enforce_limit_locked(self, conn: sqlite3.Connection) -> None:
        total = int(conn.execute("SELECT COUNT(*) FROM optimizer_jobs").fetchone()[0])
        if total <= self._max_jobs:
            return
        active_statuses = tuple(sorted(self.ACTIVE_STATUSES))
        placeholders = ", ".join("?" for _ in active_statuses)
        removable = conn.execute(
            """
            SELECT id FROM optimizer_jobs
            WHERE status NOT IN ({placeholders})
            ORDER BY created_at ASC
            """.format(placeholders=placeholders),
            active_statuses,
        ).fetchall()
        for row in removable:
            if total <= self._max_jobs:
                break
            conn.execute("DELETE FROM optimizer_jobs WHERE id = ?", (row["id"],))
            total -= 1

    def _verify_job_signature(self, row: sqlite3.Row) -> None:
        sig_stored = row["signature"]
        if sig_stored is None:
            is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
            if is_prod:
                raise JobIntegrityError(f"Job {row['id']} has no cryptographic signature.")
            return

        expected_sig = calculate_job_signature(
            job_id=row["id"],
            created_at=row["created_at"],
            request_json=row["request_json"],
            status=row["status"],
            output_dir=row["output_dir"],
            secret=self._hmac_secret
        )

        if not hmac.compare_digest(sig_stored, expected_sig):
            raise JobIntegrityError(f"Job {row['id']} signature mismatch! Data may have been tampered with.")

    def _row_to_job(self, row: sqlite3.Row) -> OptimizerJob:
        self._verify_job_signature(row)
        return OptimizerJob(
            id=str(row["id"]),
            created_at=float(row["created_at"]),
            request=_json_loads(row["request_json"], {}),
            status=str(row["status"]),
            progress=_json_loads(row["progress_json"], {}),
            best=_json_loads(row["best_json"], None),
            output_dir=str(row["output_dir"]) if row["output_dir"] else None,
            error=str(row["error"]) if row["error"] else None,
            cancel_requested=bool(row["cancel_requested"]),
            summary=_json_loads(row["summary_json"], None),
        )


OptimizerJobStore = SQLiteOptimizerJobStore


def _json_default(value: object) -> str:
    return str(value)


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _json_loads(raw: str | None, default: Any) -> Any:
    if raw in (None, ""):
        return deepcopy(default)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return deepcopy(default)