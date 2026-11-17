"""
NERO Universal Enterprise DevOps Automation Platform
Event Deduplication and Idempotency Store (A3-TRG-001)

Provides a persistent, ACID-compliant SQLite-backed idempotency and replay protection
engine for webhook deliveries and CI trigger events, surviving process restarts.
"""

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("nero.ci.idempotency")

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "idempotency_store.db")
DEFAULT_TTL_SECONDS = 600  # 10 minutes sliding window


class IdempotencyEngine:
    """ACID-compliant SQLite store for event deduplication and replay defense."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with WAL mode and row factory."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes."""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_events (
                        delivery_id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL,
                        response_payload TEXT
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_idempotency_key
                    ON idempotency_events(idempotency_key);
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires_at
                    ON idempotency_events(expires_at);
                """)
                conn.commit()
            finally:
                conn.close()

    def check_and_reserve(
        self,
        delivery_id: str,
        idempotency_key: str,
        provider: str = "generic",
        ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Atomically checks if an event is duplicate and reserves it if new.

        Returns:
            (reserved: bool, reason: str, cached_payload: Optional[Dict])
            - (True, "RESERVED", None) if newly reserved.
            - (False, "ALREADY_PROCESSING", None) if currently processing.
            - (False, "ALREADY_COMPLETED", cached_payload) if already finished within TTL.
        """
        now = time.time()
        expires_at = now + ttl_seconds

        with self._lock:
            conn = self._get_connection()
            try:
                # 1. Clean up expired records first
                conn.execute("DELETE FROM idempotency_events WHERE expires_at < ?", (now,))

                # 2. Check by delivery_id
                cursor = conn.execute(
                    "SELECT delivery_id, status, response_payload FROM idempotency_events WHERE delivery_id = ?",
                    (delivery_id,)
                )
                row = cursor.fetchone()

                # 3. If not found by delivery_id, check by idempotency_key
                if not row and idempotency_key:
                    cursor = conn.execute(
                        "SELECT delivery_id, status, response_payload FROM idempotency_events WHERE idempotency_key = ?",
                        (idempotency_key,)
                    )
                    row = cursor.fetchone()

                if row:
                    status = row["status"]
                    payload_raw = row["response_payload"]
                    cached_payload = json.loads(payload_raw) if payload_raw else None
                    if status == "processing":
                        logger.info(f"Duplicate event rejected: [{delivery_id}] is ALREADY_PROCESSING")
                        return False, "ALREADY_PROCESSING", None
                    else:
                        logger.info(f"Duplicate event recognized: [{delivery_id}] is ALREADY_COMPLETED")
                        return False, "ALREADY_COMPLETED", cached_payload

                # 4. Insert new reservation
                conn.execute(
                    """
                    INSERT INTO idempotency_events (
                        delivery_id, idempotency_key, provider, status, created_at, expires_at, response_payload
                    ) VALUES (?, ?, ?, 'processing', ?, ?, NULL)
                    """,
                    (delivery_id, idempotency_key, provider, now, expires_at)
                )
                conn.commit()
                return True, "RESERVED", None
            finally:
                conn.close()

    def mark_completed(self, delivery_id: str, response_payload: Optional[Dict[str, Any]] = None) -> None:
        """Marks event status as completed with optional cached response payload."""
        payload_str = json.dumps(response_payload) if response_payload else None
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    "UPDATE idempotency_events SET status = 'completed', response_payload = ? WHERE delivery_id = ?",
                    (payload_str, delivery_id)
                )
                conn.commit()
            finally:
                conn.close()

    def mark_failed(self, delivery_id: str, error_message: str) -> None:
        """Marks event status as failed."""
        payload_str = json.dumps({"error": error_message})
        with self._lock:
            conn = self._get_connection()
            try:
                conn.execute(
                    "UPDATE idempotency_events SET status = 'failed', response_payload = ? WHERE delivery_id = ?",
                    (payload_str, delivery_id)
                )
                conn.commit()
            finally:
                conn.close()

    def cleanup_expired(self) -> int:
        """Manually purge expired events."""
        now = time.time()
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("DELETE FROM idempotency_events WHERE expires_at < ?", (now,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
            finally:
                conn.close()
